# MEMORY.md

Project memory for Claude Code sessions. Review at session start.

## Repository Map

```
tavr-digest/
├── main.py                     # Daily digest pipeline entry point
├── config.py                   # Central config (.env loader)
├── bot_server.py               # Telegram bot (long-polling)
├── monitor.py                  # Health checks
├── sources/                    # Article fetchers (10 modules)
│   ├── pubmed.py, preprints.py, journals.py, news.py
│   ├── regulatory.py, trials.py, stocks.py
│   ├── social.py, financial.py
├── processing/                 # Dedup + Claude summarizer
│   ├── dedup.py                # SQLite SHA256 dedup
│   ├── summarizer.py           # Claude API newsletter generation
│   └── weekly.py               # Weekly digest
├── delivery/                   # Publishing
│   ├── emailer.py              # SMTP + Jinja2 templates
│   ├── beehiiv.py              # Beehiiv API v2
│   ├── website.py              # JSON push to thevalvewire-site (Vercel)
│   ├── site.py                 # GitHub Pages HTML archive
│   └── substack.py             # Substack integration
├── kanban/                     # Real-time project kanban board
│   ├── board.py                # Data generator (GitHub API → JSON)
│   └── board.html              # Self-contained frontend (dark mode)
├── podcast/                    # Podcast generation
├── templates/                  # Jinja2 HTML templates
├── static/                     # Images, audio assets
├── docs/                       # GitHub Pages site
├── .github/workflows/          # 7 workflows
│   ├── daily-digest.yml        # Daily at 12:00 UTC (6 AM CT)
│   ├── weekly-digest.yml       # Saturdays at 12:00 UTC
│   ├── kanban-update.yml       # Every 15 minutes
│   ├── weekly-podcast.yml
│   ├── daily-summary.yml
│   ├── monitor.yml
│   └── telegram-commands.yml
└── data/                       # Runtime data (dedup DB, weekly cache)
```

## GitHub Repositories (Owner: mbowdish88)

| Repo | Language | Description | Kanban Color |
|------|----------|-------------|-------------|
| tavr-digest | Python | Daily TAVR research digest (this repo) | #C4787A |
| thevalvewire-site | TypeScript | Valve Wire frontend (Vercel) | #4A90D9 |
| baseball-prospect-digest | Python | Baseball prospect digest | #50C878 |
| pptx-generator | Python | PowerPoint generator | #F5A623 |
| voice-notes | Python | Voice notes app | #9B59B6 |
| spotify-curator | Python | Spotify playlist curator | #1DB954 |
| aortic_fl_aats_2022 | — | Aortic research project | #E74C3C |

## Deployment Architecture

```
tavr-digest (this repo)
  ├── GitHub Actions → runs main.py daily
  │     ├── delivery/website.py → pushes JSON to thevalvewire-site
  │     ├── delivery/site.py → commits HTML to docs/ (GitHub Pages)
  │     └── delivery/emailer.py → sends SMTP email
  │
  ├── GitHub Actions → runs kanban/board.py every 15 min
  │     └── pushes kanban.json + board.html to thevalvewire-site
  │
  └── thevalvewire-site (separate repo)
        └── Vercel auto-deploys on every push
              ├── public/data/latest.json    (daily digest)
              ├── public/data/kanban.json    (kanban board data)
              └── public/kanban/index.html   (kanban board page)
```

## Key Env Vars

- `ANTHROPIC_API_KEY` - Claude API for newsletter synthesis
- `WEBSITE_GITHUB_TOKEN` - GitHub token with write access to thevalvewire-site (also used by kanban)
- `GITHUB_TOKEN` - Fallback for kanban data generation
- `SMTP_USER` / `SMTP_PASSWORD` - Gmail SMTP for email delivery
- `BEEHIIV_API_KEY` / `BEEHIIV_PUB_ID` - Beehiiv newsletter platform
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` - Telegram bot alerts

## Kanban Board Details

### Data Flow
1. `kanban/board.py` queries GitHub REST API for all 7 repos
2. Fetches: commits (7-day lookback), PRs (open+recent), issues, workflow runs
3. Issues with `kanban:*` labels become draggable custom task cards
4. Builds JSON with 5 columns: backlog, todo, in_progress, review, done
5. Pushes `kanban.json` to `thevalvewire-site/public/data/kanban.json`
6. Optionally pushes `board.html` to `thevalvewire-site/public/kanban/index.html`

### Frontend
- Single self-contained HTML file (no build step, no dependencies)
- Auto-polls kanban.json every 60 seconds
- Pauses polling when tab is hidden, resumes on focus
- Project filter chips toggle repos on/off
- Drag-and-drop moves custom task cards between columns (optimistic UI update)
- Toast notifications on card moves

### Adding a New Project to Kanban
Edit `PROJECTS` dict in `kanban/board.py`:
```python
"new-repo": {
    "owner": "mbowdish88",
    "repo": "new-repo",
    "color": "#HEX",
    "label": "Short Name",
},
```

## Patterns & Conventions

- **Error isolation**: Each source/delivery module catches its own errors. One failure never blocks others.
- **GitHub API pattern**: `_github_api_put_file()` in both `website.py` and `kanban/board.py` — base64 encode content, GET for SHA, PUT to create/update.
- **Retry pattern**: Claude API retries 2x with 30s delay, email retries 2x with 10s delay.
- **Dedup safety**: Articles marked seen only AFTER successful delivery (not before).
- **Template approach**: Jinja2 for emails, self-contained HTML for kanban (no framework).

## Lessons Learned

- Nitter RSS bridges are unreliable — social.py must fail gracefully
- GitHub API rate limits: 5000 req/hr with token, 60/hr without. Kanban every-15-min schedule uses ~40 requests per run (well within limits)
- Private repos require authenticated GitHub token for API access
- Vercel auto-deploys on any push to thevalvewire-site — no manual deploy needed
