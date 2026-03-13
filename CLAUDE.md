# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TAVR Digest is a daily automation agent that aggregates TAVR (Transcatheter Aortic Valve Replacement) research, news, regulatory updates, clinical trials, and stock data, then uses Claude AI to synthesize a polished newsletter digest delivered via email and Substack export.

## Running the Project

```bash
cd /Users/mbowdish/tavr-digest
source venv/bin/activate
python main.py
```

Install dependencies: `pip install -r requirements.txt`

The project runs daily at 6 AM via macOS launchd (`com.tavr-digest.agent.plist`). To manage scheduling:
- Load: `launchctl load com.tavr-digest.agent.plist`
- Unload: `launchctl unload com.tavr-digest.agent.plist`

## Architecture

The pipeline follows a linear flow: **Sources -> Dedup -> Summarize -> Deliver**

### Sources (`sources/`)
Each module fetches from one external API/feed and returns a list of article dicts:
- `pubmed.py` - NCBI eUtils API (ESearch/EFetch) with rate limiting
- `news.py` - Google News RSS with site-specific searches (TCTMD, CV Business, CMS)
- `regulatory.py` - FDA RSS feeds (press releases, MedWatch, recalls) filtered by TAVR keywords
- `trials.py` - ClinicalTrials.gov API v2 for recently updated trials
- `stocks.py` - yfinance for Edwards Lifesciences (EW) and Medtronic (MDT)

### Processing (`processing/`)
- `dedup.py` - SQLite-backed deduplication using SHA256 URL hashing. Articles are only marked seen after successful email delivery. 90-day cleanup policy.
- `summarizer.py` - Calls Claude API (Sonnet 4, 8192 max tokens) to generate Substack-ready HTML. Has `build_fallback_digest()` for plain HTML if the API fails.

### Delivery (`delivery/`)
- `emailer.py` - SMTP email with HTML+plain-text via Jinja2 templates (from `templates/digest.html`)
- `substack.py` - Generates standalone HTML pages with copy-to-clipboard JS button in `substack/`

### Configuration (`config.py`)
Central config loading from `.env`. Defines search terms, FDA filter keywords, stock tickers, and all API/SMTP settings. See `.env.example` for required variables.

## Key Design Decisions

- Each source module has isolated error handling; one failing source doesn't block others
- Claude API calls retry twice with 30s delay before falling back to plain HTML
- Email delivery retries twice with 10s delay
- Dedup marks articles as seen only after successful email send (prevents data loss)
- `main.py` skips digest generation entirely if no new articles are found after dedup

## Data Files

- `data/seen_articles.db` - SQLite dedup database
- `data/tavr_digest.log` - Application log
- `substack/tavr-digest-YYYY-MM-DD.html` - Daily generated Substack copy pages
