# CLAUDE.md — Project Kanban Board

Real-time kanban board that tracks all GitHub projects for mbowdish88.

## Running

```bash
# Generate kanban data locally (writes kanban.json)
GITHUB_TOKEN=ghp_xxx python -m kanban.board --local

# Generate and push to Vercel (thevalvewire-site repo)
GITHUB_TOKEN=ghp_xxx python -m kanban.board --push-html

# View the board locally
open kanban/board.html
```

Install: `pip install requests`

Automated: runs every 15 min via `.github/workflows/kanban-update.yml`

## Architecture

```
kanban/
├── board.py        # Data generator — queries GitHub REST API, builds JSON
├── board.html      # Self-contained frontend (HTML + CSS + JS, no build step)
└── __init__.py

.github/workflows/
└── kanban-update.yml   # Cron every 15 min, pushes to Vercel
```

### Data Flow

```
GitHub REST API (all 7 repos)
        ↓
  board.py builds kanban.json
        ↓
  Pushes via GitHub API to thevalvewire-site repo:
    ├── public/data/kanban.json      (board data)
    └── public/kanban/index.html     (board page)
        ↓
  Vercel auto-deploys on push
        ↓
  board.html polls kanban.json every 60s
```

## Tracked Repositories

| Repo | Label | Color | Language |
|------|-------|-------|----------|
| tavr-digest | Valve Wire | #C4787A | Python |
| thevalvewire-site | VW Site | #4A90D9 | TypeScript |
| baseball-prospect-digest | Baseball Digest | #50C878 | Python |
| pptx-generator | PPTX Gen | #F5A623 | Python |
| voice-notes | Voice Notes | #9B59B6 | Python |
| spotify-curator | Spotify | #1DB954 | Python |
| aortic_fl_aats_2022 | Aortic FL | #E74C3C | — |

To add a repo, edit `PROJECTS` dict in `board.py`.

## Kanban Columns

**Backlog → To Do → In Progress → Review → Done**

### Auto-populated cards (read-only)
| GitHub Activity | Column |
|---|---|
| Open issues (no kanban label) | Backlog |
| Draft PRs | In Progress |
| Failed workflow runs | In Progress |
| Open PRs (ready for review) | Review |
| Merged PRs | Done |
| Successful workflow runs | Done |
| Recent commits (last 7 days) | Done |

### Custom task cards (draggable)
Create GitHub issues with these labels to make them kanban cards:
- `kanban:backlog`
- `kanban:todo`
- `kanban:in_progress`
- `kanban:review`
- `kanban:done`

Custom cards can be dragged between columns in the UI.

## Key Files

### `board.py`
- `PROJECTS` — dict of all tracked repos with colors
- `build_kanban_data(token)` — main entry, returns full board JSON
- `_fetch_commits()`, `_fetch_prs()`, `_fetch_issues()`, `_fetch_workflows()` — per-repo fetchers
- `_assign_column(card, labels)` — maps cards to columns based on type/status
- `push_kanban(data, html_content)` — pushes JSON + HTML to thevalvewire-site via GitHub API
- `_github_api_put_file(token, path, content, message)` — base64 PUT to GitHub contents API

### `board.html`
- Self-contained: all CSS and JS inline, no external dependencies
- Dark mode (GitHub-inspired `#0d1117` theme)
- Polls `kanban.json` every 60s, pauses when tab is hidden
- Project filter chips to toggle repos
- Drag-and-drop for custom task cards with optimistic UI updates
- Toast notifications on card moves
- Responsive (works on mobile)

## Env Vars

- `GITHUB_TOKEN` or `WEBSITE_GITHUB_TOKEN` — GitHub personal access token (needs repo scope for private repos)

## Key Design Decisions

- Single HTML file with no build step — avoids framework complexity
- Server-side data generation — Python handles GitHub auth for private repos, frontend just reads JSON
- GitHub Issues for custom tasks — persistent, editable from GitHub UI or the board
- 15-min GitHub Actions schedule — ~40 API requests per run, well within 5000/hr rate limit
- Optimistic UI for drag-and-drop — card moves instantly, persists on next server refresh
