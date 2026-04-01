# CLAUDE.md — tavr-digest

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**The Valve Wire** is a production daily automation pipeline that aggregates transcatheter valve technology news — covering aortic (TAVR/TAVI), mitral (MitraClip, PASCAL, TMVR), and tricuspid (TriClip, TTVR) therapies — from academic, regulatory, financial, and social sources. It uses Claude AI to synthesize a daily newsletter, publishes to a companion website, generates a weekly podcast, and is monitored via a Telegram bot.

**Goal:** Commercialization — paid subscriptions, sponsorships, and evolving into a platform that can spin up automated digests for any niche.

**Companion website repo:** [thevalvewire-site](https://github.com/mbowdish88/thevalvewire-site) — local path: `~/projects/thevalvewire-site`

## Running the Project

```bash
cd ~/projects/tavr-digest
source venv/bin/activate
python main.py
```

Install dependencies: `pip install -r requirements.txt`

The pipeline runs daily at 6 AM Central via GitHub Actions. Manual trigger: `gh workflow run daily-digest.yml`

## Architecture

The pipeline follows: **Sources -> Dedup -> Summarize -> Deliver -> Push to Website**

### Sources (`sources/`)
Each module fetches from one external API/feed and returns a list of article dicts (`url`, `title`, `content`, `date`, `source`). Each has isolated error handling — one failing source doesn't block others.

| Module | Source | Notes |
|--------|--------|-------|
| `pubmed.py` | NCBI eUtils API (ESearch/EFetch) | 50 articles + 20 clinical trials |
| `preprints.py` | bioRxiv/medRxiv API | Filtered by relevance |
| `journals.py` | 12 RSS feeds (JACC, NEJM, Circulation, JAMA, Lancet, JTCVS, ATS, EJCTS, EHJ) | feedparser |
| `news.py` | Google News RSS | Site-specific searches (TCTMD, CV Business, CMS, SHN) |
| `regulatory.py` | FDA RSS feeds | Filtered by valve-related keywords |
| `trials.py` | ClinicalTrials.gov API v2 | 16 landmark trials monitored by NCT ID |
| `stocks.py` | yfinance | EW, MDT, ABT, BSX, AVR.AX — charts saved as PNGs |
| `social.py` | Nitter RSS bridges | 12 curated accounts — designed to fail gracefully |
| `financial.py` | SEC EDGAR 8-K filings + Google News financial RSS + yfinance news | |

### Processing (`processing/`)
| Module | Purpose |
|--------|---------|
| `dedup.py` | SQLite-backed deduplication (SHA256 URL hashing). Articles marked seen ONLY after successful email delivery. 90-day cleanup. Trials and stocks are live data, never deduped. |
| `summarizer.py` | Claude API (Sonnet 4, 16k token budget) generates HTML newsletter with executive summary, valve-specific sections, surgical vs. transcatheter comparisons, and financial analysis. Retries once with 30s delay, falls back to plain HTML. Includes major meeting detection for ACC, AHA, TCT, ESC, AATS, STS, EACTS. |
| `weekly.py` | Compiles 7 days of daily digests into a single weekly summary. |

### Delivery (`delivery/`)
| Module | Purpose | Status |
|--------|---------|--------|
| `emailer.py` | SMTP email with HTML+plain-text via Jinja2 templates. Retries once with 10s delay. | Active |
| `website.py` | Pushes structured JSON to the companion Vercel website repo. | Active |
| `site.py` | Publishes to GitHub Pages archive (`docs/`) | Active |
| `beehiiv.py` | Beehiiv API v2 newsletter delivery | Dormant — may be reinstated |
| `substack.py` | Substack integration | Available but inactive |

### Podcast (`podcast/`)
Weekly podcast generation pipeline, triggered after the weekly digest completes.

| Module | Purpose |
|--------|---------|
| `scriptwriter.py` | Claude generates a two-host podcast script from the weekly digest |
| `synthesizer.py` | OpenAI TTS voice synthesis (Nolan: "fable", Claire: "nova") |
| `assembler.py` | FFmpeg MP3 assembly with intro/outro/background music |
| `show_notes.py` | HTML + Markdown show notes |
| `transcriber.py` | Whisper API transcription |
| `publisher.py` | Publishes to GitHub Releases + RSS feed |
| `generate_assets.py` | Cover art and SVG generation |
| `audio_processing.py` | Audio utilities |

### Knowledge Base (`knowledge/`)
Injected into ALL Claude prompts for clinical context.

| Directory | Contents |
|-----------|----------|
| `papers/` | 50+ landmark study PDFs (PARTNER, COAPT, bicuspid, etc.) |
| `guidelines/` | ACC/AHA 2020 + ESC 2025 valve guidelines (PDFs + extracted text) |
| `opinions/` | Expert consensus documents |
| `guidelines_index.json` | Structured recommendations by valve type |
| `guidelines_summary.md` | Readable summary with key disagreements |

### Monitoring & Bots
| File | Purpose |
|------|---------|
| `monitor.py` | Analyzes workflow logs, sends alerts via email/Telegram |
| `telegram_bot.py` | Telegram command handler (/status, /logs, /cost, /rerun, /fix, /help) |
| `bot_server.py` | Always-on conversational Telegram bot powered by Claude (hosted on Railway) |
| `daily_summary.py` | Daily summary generator |

### Configuration (`config.py`)
Central config loading from `.env`. Defines 100+ search terms (aortic/mitral/tricuspid), 12 journal RSS feeds, 12 social accounts, 5 stock tickers, 16 landmark trial NCT IDs, SEC EDGAR CIKs, and all API settings.

## Daily Pipeline Flow (main.py)

1. Fetch from all 10 sources (isolated error handling)
2. Deduplicate via SQLite
3. Sparse data merging (fills from previous day if <5 articles)
4. Summarize with Claude API (fallback to plain HTML)
5. Save for weekly compilation
6. Publish to GitHub Pages (`docs/`)
7. Push structured JSON to website repo → Vercel auto-rebuilds
8. Send email via SMTP
9. Mark articles as seen (ONLY after successful email send)
10. Cleanup dedup entries >90 days old

## Weekly Pipeline Flow

1. Compile 7 days of daily digests (runs Saturday 6 AM CT)
2. Generate weekly HTML summary
3. Email weekly digest
4. Trigger podcast pipeline:
   - Generate script → Synthesize audio → Assemble MP3 → Show notes → Transcribe → Publish to GitHub Releases + RSS

## GitHub Actions (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `daily-digest.yml` | Daily 6 AM CT + manual | Main pipeline |
| `weekly-digest.yml` | Saturday 6 AM CT + manual | Weekly summary |
| `weekly-podcast.yml` | After weekly-digest | Podcast generation + publishing |
| `daily-summary.yml` | Scheduled | Summary generation |
| `monitor.yml` | Scheduled | Pipeline monitoring + alerts |
| `telegram-commands.yml` | Webhook | Telegram bot command handler |

All workflows restore/cache `seen_articles.db` for dedup continuity.

## Newsletter Sections (generated by Claude)
- Executive Summary (plain language, accessible to patients)
- Aortic Valve (TAVR/TAVI)
- Mitral Valve (MitraClip, PASCAL, TMVR)
- Tricuspid Valve (TriClip, TTVR)
- Surgical vs. Transcatheter Comparisons
- Financial Analysis (SEC filings, M&A, reimbursement trends)
- Valve Industry Stocks
- Clinical Trial Updates

## Key Design Decisions

- Each source module has isolated error handling; one failing source doesn't block others
- Social media monitoring uses Nitter RSS bridges — designed to fail gracefully
- Claude API retries once with 30s delay before falling back to plain HTML
- Email delivery retries once with 10s delay
- Dedup marks articles as seen ONLY after successful email send
- `main.py` skips digest generation entirely if no new articles found after dedup
- **Daily digests are the FOUNDATION.** They must NEVER be deleted after use. Weekly digest, podcast, website archive, and all future features build on top of them. They accumulate as a permanent archive.

## Infrastructure

| Component | Platform |
|-----------|----------|
| Pipeline repo | github.com/mbowdish88/tavr-digest |
| Website repo | github.com/mbowdish88/thevalvewire-site |
| Domain | thevalvewire.com (Cloudflare DNS → Vercel) |
| Website hosting | Vercel (Hobby plan) |
| Telegram bot | Railway (always-on) |
| CI/CD | GitHub Actions |
| Local paths | `~/projects/tavr-digest` and `~/projects/thevalvewire-site` |

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update tasks/lessons.md with the pattern
- Write rules for yourself that prevent the same mistake
- Review lessons at session start

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Run tests, check logs, demonstrate correctness

### 5. Autonomous Bug Fixing
- When given a bug report: just fix it
- Point at logs, errors, failing tests — then resolve them

## Task Management

1. Plan First: Write plan to tasks/todo.md with checkable items
2. Verify Plan: Check in before starting implementation
3. Track Progress: Mark items complete as you go
4. Capture Lessons: Update tasks/lessons.md after corrections

## Core Principles

- Simplicity First: Make every change as simple as possible. Minimal code impact.
- No Laziness: Find root causes. No temporary fixes. Senior developer standards.
- Minimal Impact: Only touch what's necessary. No side effects with new bugs.
