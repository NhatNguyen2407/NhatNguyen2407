"""Read public GitHub data and cache per-commit line changes.

No private repositories or email addresses are stored. A missing or failed
request never becomes a zero metric. Use --allow-pending-lines only when
preparing the first local preview without an authenticated API budget.
"""

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from fnmatch import fnmatchcase
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from common import read_json, write_json


class GitHubError(RuntimeError):
    pass


def request(path, params=None):
    url = "https://api.github.com/" + path.lstrip("/")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": "NhatNguyen2407-profile", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            return json.load(response), response.headers.get("Link", "")
    except urllib.error.HTTPError as error:
        # Do not log request headers, tokens or complete API error responses.
        raise GitHubError(f"GitHub returned HTTP {error.code} for {path.split('?')[0]}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise GitHubError(f"GitHub request did not complete: {type(error).__name__}") from None


def pages(path, params=None, limit=20):
    values = []
    for page in range(1, limit + 1):
        data, link = request(path, {**(params or {}), "per_page": 100, "page": page})
        if not isinstance(data, list):
            raise GitHubError("Expected a list from GitHub")
        values.extend(data)
        if 'rel="next"' not in link:
            return values
    raise GitHubError("Pagination limit reached; refusing to present an incomplete total")


def personal_commit(commit, username):
    author = (commit.get("author") or {}).get("login", "")
    return author.casefold() == username.casefold() and len(commit.get("parents", [])) <= 1


def count_files(files, prefix, excluded):
    added = deleted = 0
    for item in files:
        name = item.get("filename", "")
        previous = item.get("previous_filename", "")
        if prefix and not (name.startswith(prefix) or previous.startswith(prefix)):
            continue
        relative = name[len(prefix):] if prefix and name.startswith(prefix) else name
        if any(fnmatchcase(name, pattern) or fnmatchcase(relative, pattern) for pattern in excluded):
            continue
        added += int(item.get("additions", 0))
        deleted += int(item.get("deletions", 0))
    return {"added": added, "deleted": deleted}


def commit_changes(repository, sha, prefix, excluded):
    files = []
    for page in range(1, 31):
        data, link = request(f"repos/{repository}/commits/{sha}", {"per_page": 100, "page": page})
        files.extend(data.get("files", []))
        if 'rel="next"' not in link:
            # GitHub caps commit responses at 3,000 files. Treat that boundary
            # as unknown rather than silently accepting a potentially cut total.
            if len(files) >= 3000:
                raise GitHubError("Commit file limit reached")
            return count_files(files, prefix, excluded)
    raise GitHubError("Commit file pagination did not complete")


def collect(allow_pending=False):
    config = read_json("config/profile.json")
    username = config["username"]
    days = config["stats_days"]
    if days is not None and (type(days) is not int or days < 1):
        raise GitHubError("stats_days must be a positive integer or null for all-time stats")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    until = now.isoformat().replace("+00:00", "Z")
    start = (now - timedelta(days=days)).isoformat().replace("+00:00", "Z") if days is not None else None
    cache = read_json("data/commit-cache.json", {})
    fingerprint = hashlib.sha256(json.dumps([config["code_repositories"], config["excluded_paths"]], sort_keys=True).encode()).hexdigest()
    if cache.get("fingerprint") != fingerprint:
        cache = {"fingerprint": fingerprint, "commits": {}}
    active_cache = {}
    pending = []
    stats = {"stars": 0, "commits": 0, "pull_requests": None, "issues": None, "added": 0, "deleted": 0}
    languages = Counter()
    metadata = {}
    for name in dict.fromkeys([item["name"] for item in config["code_repositories"]] + config["language_repositories"]):
        repo, _ = request(f"repos/{username}/{name}")
        if repo.get("private") or repo.get("fork"):
            raise GitHubError(f"Scope must use public, non-fork repositories: {name}")
        metadata[name] = repo
    for name in config["language_repositories"]:
        values, _ = request(f"repos/{username}/{name}/languages")
        languages.update(values)
    for kind, field in [("pr", "pull_requests"), ("issue", "issues")]:
        query = f"author:{username} is:{kind} is:public created:<={until}"
        if start is not None:
            query += f" created:>={start}"
        result, _ = request("search/issues", {"q": query, "per_page": 1})
        if result.get("incomplete_results"):
            raise GitHubError("Search totals are incomplete")
        stats[field] = result["total_count"]
    to_count = []
    for item in config["code_repositories"]:
        name, prefix = item["name"], item["path"]
        repository = f"{username}/{name}"
        stats["stars"] += metadata[name].get("stargazers_count", 0)
        params = {"sha": metadata[name]["default_branch"], "author": username, "until": until}
        if start is not None:
            params["since"] = start
        if prefix:
            params["path"] = prefix.rstrip("/")
        commits = pages(f"repos/{repository}/commits", params)
        seen = set()
        for commit in commits:
            sha = commit["sha"]
            if sha in seen or not personal_commit(commit, username):
                continue
            seen.add(sha)
            stats["commits"] += 1
            to_count.append({"repository": repository, "sha": sha, "prefix": prefix})
    lines_available = True
    for commit in to_count:
        key = commit["repository"] + ":" + commit["sha"]
        change = cache.get("commits", {}).get(key)
        if change is None:
            if not lines_available:
                pending.append(commit)
                continue
            try:
                change = commit_changes(commit["repository"], commit["sha"], commit["prefix"], config["excluded_paths"])
            except GitHubError:
                if not allow_pending:
                    write_json("data/commit-cache.json", {"fingerprint": fingerprint, "commits": {**cache.get("commits", {}), **active_cache}})
                    raise
                pending.append(commit)
                lines_available = False
                continue
        active_cache[key] = change
        stats["added"] += change["added"]
        stats["deleted"] += change["deleted"]
    if pending:
        stats["added"] = stats["deleted"] = None
    output = {"updated_at": until, "since": start, "days": days, "stats": stats,
              "languages": dict(languages.most_common()),
              "code_scope": config["code_repositories"], "language_scope": config["language_repositories"],
              "pending_lines": len(pending)}
    write_json("data/commit-cache.json", {"fingerprint": fingerprint, "commits": active_cache})
    write_json("data/pending-commits.json", pending)
    write_json("data/github.json", output)
    print(f"Read public GitHub data: {stats['commits']} non-merge commits; {len(pending)} pending line-count requests.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-pending-lines", action="store_true")
    args = parser.parse_args()
    try:
        collect(args.allow_pending_lines)
    except GitHubError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
