import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {ROOT} from './chess.mjs';

export async function sendReply(result, repository, token, transport = fetch) {
  if (!/^[A-Za-z0-9-]+\/[A-Za-z0-9_.-]+$/.test(repository || '') || !token || !Number.isSafeInteger(result.issue)) throw new Error('Missing notification configuration');
  async function api(path, method = 'GET', body) {
    const response = await transport(`https://api.github.com/repos/${repository}/${path}`, {
      method, headers: {Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'},
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    if (!response.ok) throw new Error(`GitHub notification request failed: HTTP ${response.status}`);
    return response.status === 204 ? null : response.json();
  }
  // Rerunning a job may finish a missing notification, but never sends it twice.
  const marker = `<!-- profile-chess-reply:${result.issue} -->`;
  let alreadySent = false;
  for (let page = 1; page <= 10; page++) {
    const comments = await api(`issues/${result.issue}/comments?per_page=100&page=${page}`);
    if (comments.some(comment => comment.body?.includes(marker) && comment.user?.login === 'github-actions[bot]')) alreadySent = true;
    if (comments.length < 100) break;
    if (page === 10) throw new Error('Comment pagination did not finish; refusing to send a duplicate notification');
  }
  if (!alreadySent) await api(`issues/${result.issue}/comments`, 'POST', {body: marker + '\n' + result.message});
  const issue = await api(`issues/${result.issue}`);
  if (issue.state !== 'closed') await api(`issues/${result.issue}`, 'PATCH', {state: 'closed', state_reason: result.accepted ? 'completed' : 'not_planned'});
  return {alreadySent};
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const result = JSON.parse(readFileSync(ROOT + '.chess-result.json', 'utf8'));
  const sent = await sendReply(result, process.env.GITHUB_REPOSITORY, process.env.GH_TOKEN);
  console.log(sent.alreadySent ? 'Existing chess reply kept.' : 'Chess reply sent.');
}
