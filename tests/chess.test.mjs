import {test} from 'node:test';
import assert from 'node:assert/strict';
import {newGame, replay, gameStatus, parseCommand, applyCommand, notification, boardSvg, view, GOOD_GAME} from '../tools/chess.mjs';
import {sendReply} from '../tools/chess-notify.mjs';

const OWNER = 'NhatNguyen2407';
const REPO = `${OWNER}/${OWNER}`;
function command(state, uci) { return parseCommand(`chess|move|${uci}|${state.gameId}|${state.moves.length}`); }
function play(state, uci, actor, issue) { return applyCommand(state, command(state, uci), actor, issue); }
function sequence(moves, initial = newGame(OWNER, 'test-game')) {
  let state = initial;
  for (const [index, uci] of moves.entries()) {
    const result = play(state, uci, index % 2 ? OWNER : 'visitor', index + 1);
    assert.equal(result.accepted, true, uci);
    state = result.state;
  }
  return state;
}

test('visitors start as White, then only John can answer as Black', () => {
  const start = newGame(OWNER, 'test-game');
  assert.equal(view(start, REPO).moves.length, 20);
  assert.equal(play(start, 'e2e4', OWNER, 1).accepted, false);
  const visitor = play(start, 'e2e4', 'visitor', 1);
  assert.equal(visitor.accepted, true);
  assert.equal(play(visitor.state, 'e7e5', 'another-visitor', 2).accepted, false);
  assert.equal(play(visitor.state, 'c7c5', OWNER, 3).accepted, true);
});

test('two move requests for one position cannot both be accepted', () => {
  const start = newGame(OWNER, 'test-game');
  const old = command(start, 'd2d4');
  const moved = play(start, 'e2e4', 'visitor', 1).state;
  const second = applyCommand(moved, old, 'another-visitor', 2);
  assert.equal(second.accepted, false);
  assert.match(second.message, /board has changed/);
});

test('an accepted issue can be retried without applying the move again', () => {
  const start = newGame(OWNER, 'test-game');
  const moved = play(start, 'e2e4', 'visitor', 1).state;
  const retried = applyCommand(moved, command(start, 'e2e4'), 'visitor', 1);
  assert.equal(retried.duplicate, true);
  assert.equal(retried.changed, false);
  assert.equal(retried.state.moves.length, 1);
});

test('accepted visitor moves mention John; rejected moves never do', () => {
  const start = newGame(OWNER, 'test-game');
  const result = play(start, 'e2e4', 'visitor', 1);
  assert.match(notification(result, OWNER, REPO), /@NhatNguyen2407/);
  const bad = play(result.state, 'e7e5', 'visitor', 2);
  assert.doesNotMatch(notification(bad, OWNER, REPO), /@NhatNguyen2407/);
});

test('checkmate freezes move links and shows the exact thank-you message', () => {
  const state = sequence(['f2f3', 'e7e5', 'g2g4', 'd8h4']);
  assert.equal(gameStatus(replay(state)).finished, true);
  assert.equal(view(state, REPO).moves.length, 0);
  assert.ok(boardSvg(state, 'dark').includes(GOOD_GAME));
  const result = play(state, 'a2a3', 'visitor', 5);
  assert.equal(result.accepted, false);
  assert.match(result.message, /Good game! Thank you\./);
});

test('threefold repetition remains detectable because all moves are replayed', () => {
  const state = sequence(['g1f3', 'g8f6', 'f3g1', 'f6g8', 'g1f3', 'g8f6', 'f3g1', 'f6g8']);
  assert.deepEqual(gameStatus(replay(state)), {finished: true, label: 'Draw / threefold repetition'});
  assert.ok(boardSvg(state, 'light').includes(GOOD_GAME));
});

test('insufficient material and stalemate are draws', () => {
  const state = {...newGame(OWNER, 'test-game'), initialFen: '4k3/8/8/8/8/8/8/4K3 w - - 0 1'};
  assert.equal(gameStatus(replay(state)).label, 'Draw / insufficient material');
  const stalemate = {...state, initialFen: '7k/5K2/6Q1/8/8/8/8/8 b - - 0 1'};
  assert.equal(gameStatus(replay(stalemate)).label, 'Draw / stalemate');
  const fiftyMoves = {...state, initialFen: '7k/8/8/8/8/8/8/KR6 w - - 100 51'};
  assert.equal(gameStatus(replay(fiftyMoves)).label, 'Draw / fifty-move rule');
});

test('only John may start a new game, and only after the current game ends', () => {
  const active = newGame(OWNER, 'test-game');
  const restart = state => parseCommand(`chess|new|${state.gameId}|${state.moves.length}`);
  assert.equal(applyCommand(active, restart(active), OWNER, 1).accepted, false);
  const finished = sequence(['f2f3', 'e7e5', 'g2g4', 'd8h4']);
  assert.equal(applyCommand(finished, restart(finished), 'visitor', 5).accepted, false);
  const next = applyCommand(finished, restart(finished), OWNER, 6);
  assert.equal(next.state.moves.length, 0);
  assert.ok(next.archive.pgn.includes('Qh4#'));
});

test('castling, en passant and underpromotion use the same legal-move engine', () => {
  const custom = fen => ({...newGame(OWNER, 'test-game'), initialFen: fen});
  const castle = play(custom('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'), 'e1g1', 'visitor', 1);
  assert.equal(replay(castle.state).get('f1').type, 'r');
  const capture = play(custom('7k/8/8/3pP3/8/8/8/K7 w - d6 0 1'), 'e5d6', 'visitor', 1);
  assert.equal(replay(capture.state).get('d5'), undefined);
  const promotion = play(custom('7k/P7/8/8/8/8/8/K7 w - - 0 1'), 'a7a8n', 'visitor', 1);
  assert.equal(replay(promotion.state).get('a8').type, 'n');
});

test('issue titles are parsed as fixed commands, never shell or script input', () => {
  assert.equal(parseCommand('chess|move|$(touch nope)|test-game|0'), null);
  assert.equal(parseCommand('chess|move|e2e4|test-game|0\nanything'), null);
  assert.equal(parseCommand('chess|move|e2e4|../../bad|0'), null);
});

test('notification sends the owner mention and closes an accepted request', async () => {
  const calls = [];
  const transport = async (url, options) => {
    calls.push({url, ...options});
    const value = url.includes('/comments?') ? [] : {state: 'open'};
    return new Response(JSON.stringify(value), {status: 200});
  };
  await sendReply({issue: 7, accepted: true, message: '@NhatNguyen2407 a visitor has moved.'}, REPO, 'test-only', transport);
  const posts = calls.filter(call => call.method === 'POST');
  assert.equal(posts.length, 1);
  assert.match(JSON.parse(posts[0].body).body, /@NhatNguyen2407/);
  assert.deepEqual(JSON.parse(calls.find(call => call.method === 'PATCH').body), {state: 'closed', state_reason: 'completed'});
});

test('notification retries do not send another mention or alter a closed issue', async () => {
  const calls = [];
  const transport = async (url, options) => {
    calls.push(options.method);
    const value = url.includes('/comments?') ? [{body: '<!-- profile-chess-reply:7 -->', user: {login: 'github-actions[bot]'}}] : {state: 'closed'};
    return new Response(JSON.stringify(value), {status: 200});
  };
  await sendReply({issue: 7, accepted: true, message: '@NhatNguyen2407 a visitor has moved.'}, REPO, 'test-only', transport);
  assert.equal(calls.includes('POST'), false);
  assert.equal(calls.includes('PATCH'), false);
});
