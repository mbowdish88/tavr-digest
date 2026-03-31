# MEMORY.md — Project Kanban Board

Session memory for Claude Code. Review at start of each session.

## JSON Schema

### kanban.json (top level)
```json
{
  "updated_at": "ISO 8601 timestamp",
  "projects": { "<repo-name>": { "color": "#hex", "label": "Short Name", "url": "https://..." } },
  "columns": { "<column-key>": { "label": "Display Name", "cards": [...] } }
}
```

### Card object
```json
{
  "id": "repo/type/timestamp/title-slug",
  "project": "repo-name",
  "type": "commit | pr | issue | workflow | custom",
  "title": "Card title",
  "url": "https://github.com/...",
  "author": "github-username",
  "timestamp": "ISO 8601",
  "status": "open | closed | merged | draft | success | failure | committed",
  "draggable": false,
  "issue_number": null
}
```

## GitHub API Endpoints Used

Per repo (7 repos × 4 endpoints = 28 requests + issue label lookups):
- `GET /repos/{owner}/{repo}/commits?since=&per_page=20`
- `GET /repos/{owner}/{repo}/pulls?state=all&per_page=20&sort=updated`
- `GET /repos/{owner}/{repo}/issues?state=all&per_page=30&sort=updated`
- `GET /repos/{owner}/{repo}/actions/runs?per_page=10`

Push targets:
- `PUT /repos/mbowdish88/thevalvewire-site/contents/public/data/kanban.json`
- `PUT /repos/mbowdish88/thevalvewire-site/contents/public/kanban/index.html`

## Column Assignment Logic (board.py:_assign_column)

Priority order:
1. Custom tasks (`type == "custom"`) → check `kanban:*` label → fallback to backlog
2. PRs → merged=done, draft=in_progress, open=review, closed=done
3. Workflows → success/completed=done, failure=in_progress, queued/pending=in_progress
4. Issues → open=backlog, closed=done
5. Commits → always done
6. Default → backlog

## Frontend Behavior (board.html)

- `fetchData()` — tries `./data/kanban.json` then `thevalvewire.com/data/kanban.json`
- `onDataReceived()` — initializes filters on first load, renders board, updates status
- `buildFilters()` — creates clickable project chips with colored dots
- `renderBoard()` — rebuilds all columns from data, filters by active projects
- `createCardElement()` — builds card DOM with color-coded left border, type badge, status badge
- `handleDrop()` — optimistic move of draggable cards between columns
- Polling: `setInterval(fetchData, 60000)`, pauses on `visibilitychange`

## Patterns

- **GitHub API auth**: `_gh_headers(token)` returns Bearer token + API version header
- **GitHub API push**: `_github_api_put_file()` — GET file for SHA, base64 encode content, PUT with SHA for update
- **Error handling**: `_gh_get()` returns `None` on failure, callers check and skip
- **Card dedup**: issues returned by GitHub API include PRs; `_fetch_issues()` filters out `pull_request` key
- **Rate limits**: ~40 requests per run, 15-min schedule = ~160/hr (limit is 5000/hr)

## Lessons

- GitHub Issues API returns PRs too — must filter by checking `pull_request` field
- Private repos return 404 without auth token, not 403
- `_github_api_put_file` needs existing file SHA for updates (GET before PUT)
- Vercel deploys on every push to thevalvewire-site — kanban updates trigger redeploy
- Frontend `fetch()` with `cache: 'no-store'` needed to bypass browser cache on polling
