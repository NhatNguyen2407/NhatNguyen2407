import {Chess, DEFAULT_POSITION} from 'chess.js';
import {readFileSync, writeFileSync, appendFileSync} from 'node:fs';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {randomBytes} from 'node:crypto';

export const ROOT = fileURLToPath(new URL('../', import.meta.url));
export const GOOD_GAME = 'Good game! Thank you.';
const read = path => JSON.parse(readFileSync(ROOT + path, 'utf8'));
const write = (path, value) => writeFileSync(ROOT + path, JSON.stringify(value, null, 2) + '\n');
const escape = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');

export function newGame(owner, id = 'g-' + Date.now().toString(36) + '-' + randomBytes(3).toString('hex')) {
  return {version: 1, gameId: id, owner, initialFen: DEFAULT_POSITION, moves: []};
}

export function replay(state) {
  const chess = new Chess(state.initialFen);
  for (const move of state.moves) {
    chess.move({from: move.uci.slice(0, 2), to: move.uci.slice(2, 4), promotion: move.uci[4]});
  }
  return chess;
}

export function gameStatus(chess) {
  if (chess.isCheckmate()) return {finished: true, label: 'Checkmate / ' + (chess.turn() === 'w' ? 'John wins' : 'Visitors win')};
  if (chess.isStalemate()) return {finished: true, label: 'Draw / stalemate'};
  if (chess.isThreefoldRepetition()) return {finished: true, label: 'Draw / threefold repetition'};
  if (chess.isInsufficientMaterial()) return {finished: true, label: 'Draw / insufficient material'};
  if (chess.isDrawByFiftyMoves()) return {finished: true, label: 'Draw / fifty-move rule'};
  if (chess.isDraw()) return {finished: true, label: 'Draw'};
  return {finished: false, label: (chess.turn() === 'w' ? 'Visitors / White to move' : 'John / Black to move') + (chess.isCheck() ? ' / check' : '')};
}

export function parseCommand(title) {
  if (typeof title !== 'string' || title.length > 160) return null;
  const move = /^chess\|move\|([a-h][1-8][a-h][1-8][qrbn]?)\|([a-z0-9-]{1,64})\|(\d{1,5})$/.exec(title);
  if (move) return {kind: 'move', uci: move[1], gameId: move[2], ply: Number(move[3])};
  const restart = /^chess\|new\|([a-z0-9-]{1,64})\|(\d{1,5})$/.exec(title);
  return restart ? {kind: 'new', gameId: restart[1], ply: Number(restart[2])} : null;
}

export function applyCommand(state, command, actor, issue, now = new Date().toISOString()) {
  const reject = message => ({changed: false, accepted: false, message});
  if (!command || !/^[a-z0-9](?:[a-z0-9-]{0,38})$/i.test(actor)) return reject('This is not a supported chess command. Open the current board to choose a move.');
  const prior = state.moves.find(move => move.issue === issue);
  if (prior) return {changed: false, accepted: true, duplicate: true, move: prior, state};
  if (command.gameId !== state.gameId || command.ply !== state.moves.length) return reject('The board has changed since this link was created. Please choose a move from the current board.');
  const chess = replay(state);
  const status = gameStatus(chess);
  const isOwner = actor.toLowerCase() === state.owner.toLowerCase();
  if (command.kind === 'new') {
    if (!isOwner) return reject('Only John can start the next game.');
    if (!status.finished) return reject('This game is still in progress.');
    return {changed: true, accepted: true, state: newGame(state.owner), archive: {...state, result: status.label, pgn: chess.pgn()}, newGame: true};
  }
  if (status.finished) return reject(GOOD_GAME + ' This game has ended.');
  if ((chess.turn() === 'b') !== isOwner) return reject(chess.turn() === 'b' ? 'It is John\'s turn. Visitors play White.' : 'It is the visitors\' turn. John plays Black.');
  const legal = chess.moves({verbose: true}).find(move => move.from + move.to + (move.promotion || '') === command.uci);
  if (!legal) return reject('That move is not legal in the current position. Please use a current move link.');
  const moved = chess.move({from: legal.from, to: legal.to, promotion: legal.promotion});
  const move = {uci: command.uci, san: moved.san, actor, issue, at: now};
  return {changed: true, accepted: true, move, state: {...state, moves: [...state.moves, move]}};
}

export function notification(result, owner, repository) {
  const current = `https://github.com/${repository}/blob/main/docs/chess.md`;
  if (!result.accepted) return result.message + `\n\n[Open the current board](${current})`;
  if (result.newGame) return `A new game is ready. Visitors play White; John plays Black.\n\n[Open the board](${current})`;
  const status = gameStatus(replay(result.state));
  let message = `Move accepted: **${result.move.san}** (${result.move.uci}).`;
  if (result.move.actor.toLowerCase() !== owner.toLowerCase()) {
    message += `\n\n@${owner} ` + (status.finished ? 'the game has ended.' : 'a visitor has moved. It is your turn to play Black.');
  }
  if (status.finished) message += `\n\n${status.label}. **${GOOD_GAME}**`;
  return message + `\n\n[Open the current board](${current})`;
}

export function issueLink(repository, title) {
  const params = new URLSearchParams({title, body: 'Submit this issue to play the selected move. The game checks the position and whose turn it is before accepting it.'});
  return `https://github.com/${repository}/issues/new?${params}`;
}

const PIECES = {
  p: '<circle cx="12" cy="6" r="4"/><path d="M9 10H15L18 21H6Z"/><path d="M5 22H19V25H5Z"/>',
  r: '<path d="M4 2H8V6H10V2H14V6H16V2H20V10H17L18 22H6L7 10H4Z"/><path d="M4 22H20V25H4Z"/>',
  n: '<path d="M6 22L7 17L13 12L8 12L5 14L3 11L7 4L13 2L19 8L20 22Z"/><path d="M4 22H21V25H4Z"/><circle cx="12" cy="7" r="1" fill="currentColor"/>',
  b: '<path d="M12 2C4 8 5 13 10 15L6 22H18L14 15C19 13 20 8 12 2Z"/><path d="M4 22H20V25H4Z"/><path d="M10 5L14 10" fill="none"/>',
  q: '<path d="M4 5L8 11L12 3L16 11L21 5L18 21H7Z"/><path d="M4 22H21V25H4Z"/><circle cx="4" cy="4" r="2"/><circle cx="12" cy="2" r="2"/><circle cx="21" cy="4" r="2"/>',
  k: '<path d="M11 2H14V5H18V8H14V12H11V8H7V5H11Z"/><path d="M6 12C2 13 4 18 7 22H18C22 17 22 13 18 12Z"/><path d="M4 22H21V25H4Z"/>'
};

export function boardSvg(state, theme) {
  const chess = replay(state), status = gameStatus(chess);
  const p = theme === 'dark' ? {bg: '#17212c', ink: '#edf4ff', muted: '#a8b8cb', light: '#b8b6c9', dark: '#716c85'} : {bg: '#edf2f6', ink: '#283c51', muted: '#536c83', light: '#e5dcd2', dark: '#9c8fa5'};
  let body = `<rect width="320" height="330" rx="8" fill="${p.bg}"/>`;
  for (let rank = 0; rank < 8; rank++) for (let file = 0; file < 8; file++) {
    const x = 32 + file * 32, y = 28 + rank * 32;
    body += `<rect x="${x}" y="${y}" width="32" height="32" fill="${(rank + file) % 2 ? p.dark : p.light}"/>`;
    const piece = chess.board()[rank][file];
    if (piece) {
      const light = piece.color === 'w';
      body += `<g transform="translate(${x + 4} ${y + 3})" fill="${light ? '#fff4dd' : '#302939'}" stroke="${light ? '#494053' : '#d4c4db'}" color="${light ? '#494053' : '#d4c4db'}" stroke-width="1" stroke-linejoin="round">${PIECES[piece.type]}</g>`;
    }
  }
  for (let index = 0; index < 8; index++) {
    body += `<text x="${48 + index * 32}" y="17" text-anchor="middle">${'abcdefgh'[index]}</text>`;
    body += `<text x="17" y="${49 + index * 32}" text-anchor="middle">${8 - index}</text>`;
  }
  body += `<text x="160" y="307" text-anchor="middle" font-size="11">${escape(status.finished ? GOOD_GAME : status.label)}</text>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="330" viewBox="0 0 320 330" role="img" aria-labelledby="title" font-family="ui-monospace,Consolas,monospace" font-size="11" fill="${p.ink}"><title id="title">${escape(status.label + (status.finished ? '. ' + GOOD_GAME : ''))}</title>${body}</svg>\n`;
}

export function view(state, repository) {
  const chess = replay(state), status = gameStatus(chess);
  return {...status, gameId: state.gameId, ply: state.moves.length, owner: state.owner,
    moves: status.finished ? [] : chess.moves({verbose: true}).map(move => {
      const uci = move.from + move.to + (move.promotion || '');
      return {uci, san: move.san, url: issueLink(repository, `chess|move|${uci}|${state.gameId}|${state.moves.length}`)};
    }), newGameUrl: issueLink(repository, `chess|new|${state.gameId}|${state.moves.length}`)};
}

export function render(state, repository) {
  const info = view(state, repository);
  write('data/chess-view.json', info);
  for (const theme of ['dark', 'light']) writeFileSync(ROOT + `assets/chess-board-${theme}.svg`, boardSvg(state, theme));
  const version = `${state.gameId}-${state.moves.length}`;
  const image = `<picture><source media="(prefers-color-scheme: dark)" srcset="../assets/chess-board-dark.svg?v=${version}"><img src="../assets/chess-board-light.svg?v=${version}" alt="Current chess position" width="320"></picture>`;
  const lines = ['# チェス / Play chess with John', '', '[Back to my profile](../README.md)', '', image, '', '**' + info.label + '**', '',
    'Visitors play White. John (@' + state.owner + ') plays Black. This is one shared game, not a separate game per visitor.', '',
    'Choose a legal move below, then submit the pre-filled GitHub Issue. GitHub Actions validates the move and updates this board. After a visitor move is saved, the bot mentions John so he can reply.', ''];
  if (info.finished) lines.push('**' + GOOD_GAME + '**', '', `[John: start the next game](${info.newGameUrl})`);
  else lines.push('## Legal moves', '', ...info.moves.map(move => `- [${move.san} (${move.uci})](${move.url})`));
  lines.push('', '## How updates work', '', '- Move links contain the game and position revision. Old links and illegal moves are rejected.', '- Only the owner can play Black or start a new game after the current one ends.', '- Checkmate and automatic draw conditions show "' + GOOD_GAME + '" until John starts the next game.', '- Moves are processed one at a time. A second request for an old position cannot replace the accepted move.', '- A GitHub @mention generates a notification according to John\'s GitHub notification settings. Email and phone push depend on those settings.', '', 'Rules are checked with chess.js 1.4.0 (BSD-2-Clause). Piece illustrations are original SVG shapes.', '');
  writeFileSync(ROOT + 'docs/chess.md', lines.join('\n'));
  return info;
}

function event() {
  const payload = JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8'));
  const repository = process.env.GITHUB_REPOSITORY;
  const state = read('data/chess.json');
  if (repository !== `${state.owner}/${state.owner}`) throw new Error('Unexpected repository owner');
  const issue = payload.issue;
  const command = parseCommand(issue?.title);
  const result = issue?.user?.type === 'User' ? applyCommand(state, command, issue.user.login, issue.number) : {accepted: false, changed: false, message: 'Automated accounts cannot play this shared game.'};
  if (result.changed) {
    write('data/chess.json', result.state);
    if (result.archive) write('data/chess-history.json', [...read('data/chess-history.json'), result.archive]);
    render(result.state, repository);
  }
  write('.chess-result.json', {issue: issue.number, changed: result.changed, accepted: result.accepted,
    message: notification(result, state.owner, repository)});
  if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, `changed=${Boolean(result.changed)}\n`);
  console.log(result.changed ? 'Accepted a chess action.' : 'No chess state change; a reply is prepared.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv[2] === 'render') {
    const state = read('data/chess.json');
    render(state, `${state.owner}/${state.owner}`);
  } else if (process.argv[2] === 'event') event();
  else throw new Error('Use render or event.');
}
