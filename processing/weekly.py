"""Weekly digest — synthesizes the week's daily digests into a single summary."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

from anthropic import Anthropic

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a medical literature and market analyst specializing in structural heart \
disease. You produce "The Valve Wire Weekly" by E. Nolan Beckett — a weekly summary \
newsletter that distills the week's daily digests into a single, comprehensive overview. \
Your audience includes cardiac surgeons, interventional cardiologists, trainees, patients, \
industry stakeholders, and regulatory agencies. Write in a polished, engaging newsletter \
style — authoritative but approachable. Focus on the most important developments and \
emerging trends across the full week."""

WEEKLY_PROMPT = """\
Produce a weekly summary newsletter from the daily Valve Wire digests below. This covers \
{start_date} through {end_date}. It will be published as "The Valve Wire Weekly" on Beehiiv.

## Format Rules (Beehiiv/email compatibility)
- Use ONLY these HTML tags: <h2>, <h3>, <p>, <ul>, <li>, <ol>, <a>, <strong>, \
<em>, <blockquote>, <hr>
- Do NOT use <table>, <div>, <span>, <style>, or any CSS.
- Every section of text should be wrapped in <p> tags.
- Use <hr> between major sections.

## Content Instructions
- Begin with an <h2>Week in Review</h2> — a 4-6 sentence executive summary of the \
week's most significant developments across all valve types. Written in plain language \
accessible to patients.

- Then organize into these sections using <h2> headers (omit sections with no content):
  - Week in Review (always include)
  - Top Stories — The 3-5 most impactful developments of the week, with context
  - Aortic Valve (TAVR/TAVI) — Week's highlights
  - Mitral Valve — Week's highlights (repair and replacement)
  - Tricuspid Valve — Week's highlights (repair and replacement)
  - Clinical Trials Update — Status changes, new results, enrollment milestones. \
    Highlight landmark trials: REPAIR-MR, PRIMATY, TRILUMINATE, CLASP TR, APOLLO, \
    TRISCEND, PARTNER, COAPT, Evolut
  - Surgical vs. Transcatheter — Any comparative studies or debates
  - Market & Industry — Stock performance trends, M&A, earnings, regulatory
  - Week Ahead — What to watch next week

- Synthesize across the full week — don't just list each day's content separately. \
Connect the dots, identify trends, and tell the story of the week.
- Flag practice-changing findings with <strong>[NOTABLE]</strong>.
- Include hyperlinks where available.
- Tone: expert, analytical, but readable. Like a front-office weekly briefing.
- End with a brief closing thought.

## Daily Digests This Week
{digests_section}

Produce the weekly summary newsletter HTML now."""


def save_daily_digest(digest_html: str, digest_date: date = None):
    """Save a daily digest for later weekly compilation."""
    digest_date = digest_date or date.today()
    filepath = config.WEEKLY_DIR / f"{digest_date.isoformat()}.html"
    filepath.write_text(digest_html, encoding="utf-8")
    logger.info(f"Saved daily digest for weekly compilation: {filepath.name}")


def get_week_digests(end_date: date = None) -> list[dict]:
    """Load all daily digests from the past week."""
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)

    digests = []
    current = start_date
    while current <= end_date:
        filepath = config.WEEKLY_DIR / f"{current.isoformat()}.html"
        if filepath.exists():
            digests.append({
                "date": current.isoformat(),
                "day": current.strftime("%A"),
                "content": filepath.read_text(encoding="utf-8"),
            })
        current += timedelta(days=1)

    logger.info(f"Found {len(digests)} daily digests for week of {start_date} to {end_date}")
    return digests


def create_weekly_digest(end_date: date = None) -> str:
    """Generate a weekly summary from the week's daily digests."""
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)

    digests = get_week_digests(end_date)
    if not digests:
        logger.warning("No daily digests found for weekly summary.")
        return None

    # Format digests for the prompt
    digest_parts = []
    for d in digests:
        digest_parts.append(
            f"### {d['day']}, {d['date']}\n"
            f"{d['content']}\n"
            f"{'=' * 60}\n"
        )
    digests_section = "\n".join(digest_parts)

    prompt = WEEKLY_PROMPT.format(
        start_date=start_date.strftime("%B %d"),
        end_date=end_date.strftime("%B %d, %Y"),
        digests_section=digests_section,
    )

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    logger.info(
        f"Generating weekly summary from {len(digests)} daily digests "
        f"({start_date} to {end_date}) with {config.CLAUDE_MODEL}"
    )

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=16384,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    summary = message.content[0].text
    logger.info(
        f"Weekly digest generated: {len(summary)} chars, "
        f"tokens: {message.usage.input_tokens} in / {message.usage.output_tokens} out"
    )

    return summary


def clear_week_digests(end_date: date = None):
    """Remove daily digest files after weekly summary is published."""
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)

    removed = 0
    current = start_date
    while current <= end_date:
        filepath = config.WEEKLY_DIR / f"{current.isoformat()}.html"
        if filepath.exists():
            filepath.unlink()
            removed += 1
        current += timedelta(days=1)

    logger.info(f"Cleared {removed} daily digest files")
