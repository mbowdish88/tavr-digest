# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Valve Wire is a daily automation agent that aggregates transcatheter valve technology news — covering aortic (TAVR/TAVI), mitral (MitraClip, PASCAL, TMVR), and tricuspid (TriClip, TTVR) therapies — from academic, regulatory, financial, and social sources. It uses Claude AI to synthesize a polished daily newsletter, then publishes via Beehiiv and email.

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

## Running the Project

```bash
cd /Users/mbowdish/tavr-digest
source venv/bin/activate
python main.py
```

Install dependencies: `pip install -r requirements.txt`

The project runs daily at 6 AM Central via GitHub Actions. Manual trigger: `gh workflow run daily-digest.yml`

### Kanban Board

```bash
# Generate kanban data locally (requires GITHUB_TOKEN env var)
python -m kanban.board --local

# Generate and push to Vercel
python -m kanban.board --push-html
```

Runs automatically every 15 min via `.github/workflows/kanban-update.yml`.

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

## Architecture

The digest pipeline follows: **Sources -> Dedup -> Summarize -> Deliver**

### Sources (`sources/`)
Each module fetches from one external API/feed and returns a list of article dicts:
- `pubmed.py` - NCBI eUtils API (ESearch/EFetch) with rate limiting
- `preprints.py` - bioRxiv/medRxiv API, filtered by relevance to search terms
- `journals.py` - RSS feeds from JACC, NEJM, Circulation, JAMA, Lancet, JTCVS, ATS, EJCTS, EHJ
- `news.py` - Google News RSS with site-specific searches (TCTMD, CV Business, CMS, SHN)
- `regulatory.py` - FDA RSS feeds filtered by valve-related keywords
- `trials.py` - ClinicalTrials.gov API v2
- `stocks.py` - yfinance for EW, MDT, ABT, BSX, AVR.AX
- `social.py` - Free Nitter RSS bridges for curated Twitter/X accounts
- `financial.py` - SEC EDGAR 8-K filings, Google News financial RSS, yfinance news

### Processing (`processing/`)
- `dedup.py` - SQLite-backed deduplication using SHA256 URL hashing. Articles only marked seen after successful email delivery. 90-day cleanup.
- `summarizer.py` - Calls Claude API (16384 max tokens) to generate newsletter HTML with executive summary, valve-specific sections, surgical vs. transcatheter comparisons, and financial analysis. Has `build_fallback_digest()` for plain HTML if API fails.

### Delivery (`delivery/`)
- `beehiiv.py` - Publishes via Beehiiv API v2 (automated newsletter delivery to subscribers)
- `emailer.py` - SMTP email with HTML+plain-text via Jinja2 templates
- `website.py` - Pushes JSON data to `mbowdish88/thevalvewire-site` repo via GitHub API for Vercel deployment
- `site.py` - Publishes HTML digests to GitHub Pages (`docs/` folder)

### Kanban Board (`kanban/`)
Real-time project tracker across all GitHub repositories:
- `board.py` - Python data generator. Queries GitHub REST API for all 7 repos (commits, PRs, issues, workflow runs). Builds `kanban.json` and pushes to thevalvewire-site via GitHub API.
- `board.html` - Self-contained frontend (HTML/CSS/JS in one file). Dark-mode dashboard with 5 columns, project filter chips, drag-and-drop for custom tasks, auto-polls every 60s.

**Custom tasks:** Create GitHub issues with `kanban:backlog`, `kanban:todo`, `kanban:in_progress`, `kanban:review`, or `kanban:done` labels. These appear as draggable cards on the board.

**Card-to-column mapping:**
| Activity | Column |
|---|---|
| Open issues (no kanban label) | Backlog |
| Draft PRs | In Progress |
| Open PRs (ready) | Review |
| Merged PRs / successful workflows | Done |
| Failed workflows | In Progress |
| Issues with `kanban:*` labels | Per label |

**Adding a new project:** Edit `PROJECTS` dict in `kanban/board.py`:
```python
"new-repo": {
    "owner": "mbowdish88",
    "repo": "new-repo",
    "color": "#HEX",
    "label": "Short Name",
},
```

### Configuration (`config.py`)
Central config loading from `.env`. Defines search terms for aortic/mitral/tricuspid valves, journal RSS feeds, social media accounts, stock tickers, SEC EDGAR CIKs, and all API settings.

## Key Env Vars

- `ANTHROPIC_API_KEY` - Claude API for newsletter synthesis
- `WEBSITE_GITHUB_TOKEN` - GitHub token with write access to thevalvewire-site (also used by kanban)
- `GITHUB_TOKEN` - Fallback for kanban data generation
- `SMTP_USER` / `SMTP_PASSWORD` - Gmail SMTP for email delivery
- `BEEHIIV_API_KEY` / `BEEHIIV_PUB_ID` - Beehiiv newsletter platform
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` - Telegram bot alerts

## Patterns & Conventions

- **Error isolation**: Each source/delivery module catches its own errors. One failure never blocks others.
- **GitHub API pattern**: `_github_api_put_file()` in both `website.py` and `kanban/board.py` — base64 encode content, GET for SHA, PUT to create/update.
- **Retry pattern**: Claude API retries 2x with 30s delay, email retries 2x with 10s delay.
- **Dedup safety**: Articles marked seen only AFTER successful delivery (not before).
- **Template approach**: Jinja2 for emails, self-contained HTML for kanban (no framework).
- **Nitter RSS bridges** are unreliable — social.py must fail gracefully.
- **GitHub API rate limits**: 5000 req/hr with token, 60/hr without. Kanban every-15-min schedule uses ~40 requests per run.
- **Private repos** require authenticated GitHub token for API access.
- **Vercel** auto-deploys on any push to thevalvewire-site — no manual deploy needed.

## Key Design Decisions

- Each source module has isolated error handling; one failing source doesn't block others
- Claude API calls retry twice with 30s delay before falling back to plain HTML
- Email delivery retries twice with 10s delay
- Dedup marks articles as seen only after successful email send
- Beehiiv publishing failure does not block email delivery
- `main.py` skips digest generation entirely if no new articles are found after dedup
- Kanban board is a single self-contained HTML file — no build step, no framework

## Newsletter Sections (generated by Claude)
- Executive Summary (plain language, accessible to patients)
- Aortic Valve (TAVR/TAVI)
- Mitral Valve (MitraClip, PASCAL, TMVR)
- Tricuspid Valve (TriClip, TTVR)
- Surgical vs. Transcatheter Comparisons
- Financial Analysis (SEC filings, M&A, reimbursement trends)
- Valve Industry Stocks
- Clinical Trial Updates

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update tasks/lessons.md with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes -- don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests -- then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. Plan First: Write plan to tasks/todo.md with checkable items
2. Verify Plan: Check in before starting implementation
3. Track Progress: Mark items complete as you go
4. Explain Changes: High-level summary at each step
5. Document Results: Add review section to tasks/todo.md
6. Capture Lessons: Update tasks/lessons.md after corrections

## Core Principles

- Simplicity First: Make every change as simple as possible. Impact minimal code.
- No Laziness: Find root causes. No temporary fixes. Senior developer standards.
- Minimal Impact: Only touch what's necessary. No side effects with new bugs.
