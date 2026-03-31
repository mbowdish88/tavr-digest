# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**The Valve Wire** is a production medical newsletter and podcast automation platform that aggregates transcatheter valve technology news — covering aortic (TAVR/TAVI), mitral (MitraClip, PASCAL, TMVR), and tricuspid (TriClip, TTVR) therapies — from 9+ academic, regulatory, financial, and social sources. It uses Claude AI to synthesize polished daily and weekly newsletters, generates a weekly two-host podcast via OpenAI TTS, and publishes via email, Beehiiv, GitHub Pages, and a Vercel website.

## Running the Project

```bash
# Daily digest
python main.py

# Weekly summary (compiles Mon-Fri daily digests)
python main.py --weekly

# Weekly podcast (generates script, TTS, assembles audio)
python main.py --podcast
```

Install dependencies: `pip install -r requirements.txt`
System dependency for podcast: `ffmpeg`

The project runs daily at 6 AM Central via GitHub Actions. Manual trigger: `gh workflow run daily-digest.yml`

## Architecture

The pipeline follows: **Sources -> Dedup -> Summarize -> Deliver**

```
9 Sources (pubmed, news, regulatory, trials, stocks, preprints, journals, social, financial)
    |
Dedup DB (SQLite, 90-day rolling, SHA256 URL hashing)
    |
Claude API (create_digest + fallback to plain HTML)
    |
4 Delivery Channels
    ├── Email (SMTP via Jinja2 templates)
    ├── Beehiiv (API v2)
    ├── GitHub Pages (docs/)
    └── Vercel Website (JSON API push)

Weekly: Compiles daily digests (Mon-Fri) -> Claude weekly summary -> Email + Pages
Podcast: Claude script -> OpenAI TTS -> pydub assembly -> GitHub Releases + RSS
```

### Sources (`sources/`)
Each module fetches from one external API/feed and returns a list of article dicts:
- `pubmed.py` - NCBI eUtils API (ESearch/EFetch) with rate limiting (0.1s w/ key, 0.34s without)
- `preprints.py` - bioRxiv/medRxiv API with keyword relevance filtering
- `journals.py` - RSS feeds from 11 journals (JACC, NEJM, Circulation, JAMA, Lancet, JTCVS, ATS, EJCTS, EHJ)
- `news.py` - Google News RSS with site-specific searches (TCTMD, CV Business, CMS, SHN)
- `regulatory.py` - FDA RSS feeds (press releases, MedWatch, recalls) filtered by 23 valve keywords
- `trials.py` - ClinicalTrials.gov API v2 + 10 hardcoded landmark trials always monitored
- `stocks.py` - yfinance for EW, MDT, ABT, BSX, AVR.AX with QuickChart.io chart generation
- `social.py` - Free Nitter RSS bridges for 12 curated Twitter/X accounts (fails gracefully)
- `financial.py` - SEC EDGAR 8-K filings, Google News financial RSS, yfinance news

### Processing (`processing/`)
- `dedup.py` - SQLite-backed deduplication using SHA256 URL hashing. Articles only marked seen after successful email delivery. 90-day cleanup.
- `summarizer.py` - Calls Claude API (16384 max tokens) to generate newsletter HTML with executive summary, valve-specific sections, surgical vs. transcatheter comparisons, and financial analysis. Has `build_fallback_digest()` for plain HTML if API fails.
- `weekly.py` - Compiles Mon-Fri daily digests into a weekly summary via Claude

### Delivery (`delivery/`)
- `emailer.py` - SMTP email with HTML+plain-text via Jinja2 templates
- `beehiiv.py` - Publishes via Beehiiv API v2 (automated newsletter delivery to subscribers)
- `site.py` - GitHub Pages publication to `docs/` directory
- `website.py` - Builds structured JSON (article classification, OG images, stock data, podcast episodes) and pushes to `mbowdish88/thevalvewire-site` via GitHub API for Vercel deployment. Merges with previous day's data when content is sparse (<5 articles).
- `substack.py` - Substack integration

### Podcast (`podcast/`)
Full podcast generation pipeline with two AI hosts (Nolan and Claire):
- `scriptwriter.py` - Claude-generated conversational two-host dialogue script
- `synthesizer.py` - OpenAI TTS synthesis (voices: "fable" for Nolan, "nova" for Claire)
- `audio_processing.py` - Voice processing (EQ, compression, normalization via scipy)
- `assembler.py` - pydub-based audio assembly with intro/outro music, transitions, background beds
- `transcriber.py` - OpenAI Whisper transcription
- `show_notes.py` - Markdown + HTML show notes generation
- `publisher.py` - GitHub Releases upload + RSS feed update
- `generate_assets.py` - Podcast cover art + landing page generation

### Operational (`bot_server.py`, `telegram_bot.py`, `monitor.py`, `daily_summary.py`)
- `bot_server.py` - Always-on Telegram bot (deployed on Railway) for natural language workflow control
- `telegram_bot.py` - Event-triggered Telegram command handler (GitHub Actions variant)
- `monitor.py` - CI/CD pipeline monitor with Claude-powered log analysis and auto-fix capability
- `daily_summary.py` - Morning workflow status summaries via Telegram

### Knowledge Base (`knowledge/`)
Medical reference library injected into Claude prompts for accuracy:
- `guidelines/` - ACC/AHA 2020 and ESC 2025 valve guidelines (PDF + text)
- `papers/` - 20+ landmark studies from NEJM, JAMA, etc.
- `guidelines_summary.md` / `.html` - Extracted guidelines summaries
- `guidelines_index.json` - Searchable index

### Configuration (`config.py`)
Central config loading from `.env` (~301 lines). Defines:
- **API keys**: Anthropic, NCBI, OpenAI, Beehiiv, Telegram
- **Search terms**: 100+ terms across aortic, mitral, tricuspid, and general categories
- **Data sources**: 11 journal RSS feeds, 3 FDA feeds, 4 news sites, 12 Twitter accounts, 5 stock tickers, 4 SEC EDGAR companies, 10 landmark trial NCT IDs
- **Podcast settings**: Host voices, episode DB path, RSS URL
- **Paths**: data/, templates/, static/, docs/

## CI/CD Workflows (`.github/workflows/`)

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `daily-digest.yml` | Daily 12:00 UTC (6 AM CT) | Fetch sources, generate digest, email, publish |
| `weekly-digest.yml` | Saturday 12:00 UTC | Compile weekly summary from daily digests |
| `weekly-podcast.yml` | After weekly-digest succeeds | Generate podcast (TTS + assembly), 45min timeout |
| `monitor.yml` | On workflow completion | Analyze logs with Claude, alert on failures |
| `daily-summary.yml` | Morning | Status report of all workflows via Telegram |
| `telegram-commands.yml` | Disabled (moved to Railway) | Was: Telegram command polling |

All workflows use Python 3.12 and cache the SQLite dedup DB between runs.

## Key Design Decisions

- Each source module has isolated error handling; one failing source doesn't block others
- Social media monitoring uses free Nitter RSS bridges (may be unreliable — designed to fail gracefully)
- Claude API calls retry twice with 30s delay before falling back to plain HTML
- Email delivery retries twice with 10s delay
- Dedup marks articles as seen only after successful email send
- Beehiiv publishing failure does not block email delivery
- `main.py` skips digest generation entirely if no new articles are found after dedup
- Stocks and trials are not deduped (live data refreshed each run)
- Podcast synthesis retries failed segments after 5s delay, proceeds with partial output
- Weekend/holiday publish check (skips non-business days unless overridden)

## Dependencies

### Python (`requirements.txt`)
| Package | Purpose |
|---------|---------|
| anthropic>=0.84.0 | Claude API client |
| requests>=2.31.0 | HTTP requests |
| feedparser>=6.0.12 | RSS feed parsing |
| python-dotenv>=1.0.0 | .env file loading |
| jinja2>=3.1.0 | Email template rendering |
| yfinance>=0.2.36 | Stock data |
| openai>=1.0.0 | TTS + Whisper |
| pydub>=0.25.1 | Audio assembly |
| mutagen>=1.47.0 | MP3 ID3 tagging |
| cairosvg>=2.7.0 | SVG to PNG conversion |
| scipy>=1.11.0 | Audio processing (EQ, compression) |

### System
- Python 3.12, ffmpeg, libcairo

### Bot-only (`requirements-bot.txt`)
- anthropic>=0.80.0, requests>=2.31.0

## Data Flow and File Structure

```
data/
├── seen_articles.db          # SQLite dedup database (cached in CI)
├── valve_wire.log            # Application log
├── weekly/                   # Saved daily digests for weekly compilation
├── podcast/                  # Episode MP3s and segments
│   ├── segments/             # Per-date speaker segments
│   └── *.mp3                 # Final episodes
└── podcast_episodes.json     # Episode history & metadata

docs/                         # GitHub Pages (committed by CI)
├── digest/YYYY-MM-DD/        # Daily digest archives + chart PNGs
├── weekly/YYYY-MM-DD/        # Weekly summaries
└── podcast/                  # Podcast landing + metadata

templates/
├── digest.html               # Email template (navy/gold, Georgia serif)
├── podcast_rss.xml           # iTunes-compatible RSS feed
├── podcast_landing.html      # Podcast landing page
└── site_index.html           # GitHub Pages index

static/
├── banner.jpg, cover.jpg     # Email/site images
├── podcast-cover.svg/.png    # Podcast artwork
├── valve-wire-banner.svg     # Branded banner
└── audio/                    # Intro, outro, transition, background WAVs
```

## Newsletter Sections (generated by Claude)
- Executive Summary (plain language, accessible to patients)
- Aortic Valve (TAVR/TAVI)
- Mitral Valve (MitraClip, PASCAL, TMVR)
- Tricuspid Valve (TriClip, TTVR)
- Surgical vs. Transcatheter Comparisons
- Financial Analysis (SEC filings, M&A, reimbursement trends)
- Valve Industry Stocks
- Clinical Trial Updates

### Editorial Guidelines (embedded in Claude prompts)
- **Journal Hierarchy**: NEJM > JAMA > JACC > Lancet > EHJ > others
- **Critical Perspective**: Flag study limitations (non-randomized, small sample, single-center, industry sponsorship)
- **Balance**: Present both favorable and critical viewpoints
- **Skepticism**: Emphasize when long-term data is lacking
- **Durability**: Note devices awaiting follow-up studies

## Error Handling Patterns

1. **Source isolation**: Each source in `main.py` wrapped in try/except; failures logged, pipeline continues
2. **Claude retry**: 2 attempts, 30s delay, then `build_fallback_digest()` plain HTML
3. **Email retry**: 2 attempts, 10s delay; articles NOT marked seen on failure (retry safety)
4. **Podcast retry**: Failed TTS segments retried after 5s; partial output accepted
5. **Rate limiting**: PubMed (0.1s/0.34s), SEC EDGAR (custom User-Agent), all requests have explicit timeouts (15-60s)
6. **Logging**: `logging.getLogger(__name__)` pattern, both file + stdout, configurable LOG_LEVEL

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
