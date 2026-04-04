"""Weekly digest — standalone weekly newsletter with full research, trials, and market data."""

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
disease. You produce "The Valve Wire Weekly" by E. Nolan Beckett — a comprehensive \
standalone weekly newsletter covering transcatheter valve technology. Your audience \
includes cardiac surgeons, interventional cardiologists, trainees, patients, industry \
stakeholders, and regulatory agencies.

IMPORTANT: This newsletter must be completely self-contained. The reader has NOT seen \
any daily digests this week. Every finding, trial update, and market movement must be \
fully explained with context. Include hyperlinks to every research article, trial, and \
news source mentioned. This is the reader's only source for the week — make it thorough.

CRITICAL EDITORIAL STANCE: Many structural heart technologies have gotten ahead of \
the science and clinical guidelines. You must be BALANCED and CIRCUMSPECT:
- Always present competing arguments for and against favorable findings
- Flag study limitations: non-randomized designs, industry sponsorship, short follow-up, \
small samples, single-center data
- When reporting favorable transcatheter outcomes, note durability concerns, patient \
selection biases, complication rates, and surgical alternatives
- Never present transcatheter superiority as settled when long-term data or guidelines \
don't support it
- Reference critical perspectives where relevant (Bowdish, Badhwar, Mehaffey, Kaul, \
Miller, Chikwe have published on therapies outpacing evidence)
- Tone: expert skepticism — enthusiastic about real advances but always questioning. \
Think peer review, not press release."""

WEEKLY_PROMPT = """\
Produce a comprehensive standalone weekly newsletter from all the data below. This covers \
{start_date} through {end_date}. It will be published as "The Valve Wire Weekly" on Beehiiv.

The reader has NOT seen any daily digests — this must be completely self-contained with \
full context, explanations, and hyperlinks for everything mentioned.

## Format Rules (Beehiiv/email compatibility)
- Use ONLY these HTML tags: <h2>, <h3>, <p>, <ul>, <li>, <ol>, <a>, <strong>, \
<em>, <blockquote>, <hr>
- Do NOT use <table>, <div>, <span>, <style>, or any CSS.
- Every section of text should be wrapped in <p> tags.
- Use <hr> between major sections.
- EVERY research article, trial, and news item MUST include a clickable hyperlink.

## Content Sections (use <h2> headers, omit sections with no content)

### 1. <h2>Week in Review</h2>
- 5-7 sentence executive summary of the week's most significant developments
- Written in plain language accessible to patients
- Mention the single most important story first

### 2. <h2>Top Stories This Week</h2>
- The 3-5 most impactful developments with full context and analysis
- Each story gets its own <h3> with a descriptive headline
- Include hyperlinks to the source article/study for each story
- Flag practice-changing findings with <strong>[NOTABLE]</strong>

### 3. <h2>Aortic Valve (TAVR/TAVI)</h2>
- All TAVR-related research, news, and developments from the week
- Link to every study mentioned: <a href="URL">Study Title</a>
- Include study design, sample size, key findings

### 4. <h2>Mitral Valve (Repair & Replacement)</h2>
- Cover both repair (MitraClip, PASCAL, REPAIR-MR, PRIMATY) and replacement (Tendyne, Intrepid, SAPIEN M3)
- Link to every study and news item

### 5. <h2>Tricuspid Valve (Repair & Replacement)</h2>
- Cover both repair (TriClip, TRILUMINATE, CLASP TR) and replacement (Evoque, TRISCEND, GATE)
- Link to every study and news item

### 6. <h2>Surgical vs. Transcatheter Comparisons</h2>
- Any comparative studies or debate points from the week
- Highlight where surgical and transcatheter approaches diverge or converge on evidence

### 7. <h2>Clinical Trials Update</h2>
- Group by valve type with <h3> subheadings
- For each trial: name, NCT ID (linked to ClinicalTrials.gov), status, phase, enrollment, sponsor
- Highlight landmark trials: REPAIR-MR, PRIMATY, TRILUMINATE, CLASP TR, APOLLO, \
TRISCEND, PARTNER, COAPT, Evolut
- Note any status changes or milestones this week

### 8. <h2>Valve Industry Stocks — Weekly Performance</h2>
- For each company: weekly price change ($ and %), current price, and brief analysis
- Reference the embedded stock charts
- Include analyst targets and upcoming earnings dates
- Contextualize moves with industry news
- Mention that {private_companies} are private (no public data)

### 9. <h2>Regulatory & Policy</h2>
- FDA actions, CMS reimbursement, policy changes

### 10. <h2>Weekend News</h2>
- Saturday/Sunday developments — any breaking news, conference updates, or announcements

### 11. <h2>Week Ahead</h2>
- What to watch next week: upcoming conferences, earnings, trial readouts, FDA dates

### 12. <h2>All Research & Sources This Week</h2>
- Complete bulleted list of EVERY research article and news item referenced in this newsletter
- Each item must be a clickable hyperlink: <a href="URL">Title</a> — Source, Date
- Group by: Research Articles | News & Regulatory
- Do NOT re-list clinical trials here — they are covered in the Clinical Trials Update section above

## Data Sources

### Daily Digests (Monday–Friday)
{digests_section}

### Weekend News
{weekend_section}

### Stock Performance Data
{stock_section}

### Clinical Trial Updates
{trials_section}

Produce the comprehensive weekly newsletter HTML now."""


def save_daily_digest(
    digest_html: str,
    digest_date: date = None,
    structured_sidecar: dict = None,
):
    """Save a daily digest and optional structured sidecar for later weekly compilation."""
    digest_date = digest_date or date.today()
    filepath = config.WEEKLY_DIR / f"{digest_date.isoformat()}.html"
    filepath.write_text(digest_html, encoding="utf-8")
    logger.info(f"Saved daily digest for weekly compilation: {filepath.name}")

    if structured_sidecar:
        json_path = config.WEEKLY_DIR / f"{digest_date.isoformat()}.json"
        json_path.write_text(
            json.dumps(structured_sidecar, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(
            f"Saved structured sidecar: {json_path.name} "
            f"({len(structured_sidecar.get('articles', []))} articles)"
        )


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


def get_week_sidecars(end_date: date = None) -> list[dict]:
    """Load all structured JSON sidecars from the past week.

    Returns a flat list of article metadata dicts from all daily sidecars.
    """
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)

    all_articles = []
    current = start_date
    while current <= end_date:
        json_path = config.WEEKLY_DIR / f"{current.isoformat()}.json"
        if json_path.exists():
            try:
                sidecar = json.loads(json_path.read_text(encoding="utf-8"))
                all_articles.extend(sidecar.get("articles", []))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load sidecar {json_path.name}: {e}")
        current += timedelta(days=1)

    logger.info(f"Loaded {len(all_articles)} article metadata records from weekly sidecars")
    return all_articles


def _fetch_weekend_news() -> str:
    """Fetch Saturday/Sunday news for the weekly digest."""
    from sources import news as news_module

    try:
        articles = news_module.fetch_recent()
        if not articles:
            return "No weekend news found."

        parts = []
        for a in articles:
            parts.append(
                f"Title: {a['title']}\n"
                f"Source: {a.get('source_name', 'Unknown')}\n"
                f"Date: {a['pub_date']}\n"
                f"URL: {a['url']}\n"
                f"Snippet: {a.get('snippet', '')}\n"
            )
        return "\n---\n".join(parts)
    except Exception as e:
        logger.warning(f"Weekend news fetch failed: {e}")
        return "Weekend news unavailable."


def _fetch_stock_data() -> tuple[str, dict]:
    """Fetch current stock data with weekly performance for the weekly digest.

    Returns (formatted_text, raw_stock_data) tuple.
    """
    from sources import stocks as stocks_module
    from processing.summarizer import _format_stock_data

    try:
        stock_data = stocks_module.fetch_stock_data()
        if not stock_data:
            return "Stock data unavailable.", {}
        return _format_stock_data(stock_data), stock_data
    except Exception as e:
        logger.warning(f"Stock data fetch failed: {e}")
        return "Stock data unavailable.", {}


def _fetch_trial_updates() -> str:
    """Fetch current trial data for the weekly digest."""
    from sources import trials as trials_module
    from processing.summarizer import _format_trials

    try:
        trial_updates = trials_module.fetch_trial_updates(days=7)
        landmark = trials_module.fetch_landmark_trials()
        seen = {t["nct_id"] for t in trial_updates}
        for t in landmark:
            if t["nct_id"] not in seen:
                trial_updates.append(t)

        if not trial_updates:
            return "No trial updates this week."
        return _format_trials(trial_updates)
    except Exception as e:
        logger.warning(f"Trial updates fetch failed: {e}")
        return "Trial data unavailable."


def create_weekly_digest(end_date: date = None) -> tuple[str, dict]:
    """Generate a comprehensive standalone weekly summary.

    Returns (weekly_html, stock_data) tuple.
    """
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)

    digests = get_week_digests(end_date)
    if not digests:
        logger.warning("No daily digests found for weekly summary.")
        return None, {}

    # Format daily digests
    digest_parts = []
    for d in digests:
        digest_parts.append(
            f"### {d['day']}, {d['date']}\n"
            f"{d['content']}\n"
            f"{'=' * 60}\n"
        )
    digests_section = "\n".join(digest_parts)

    # Fetch fresh data for the weekly
    logger.info("Fetching weekend news...")
    weekend_section = _fetch_weekend_news()

    logger.info("Fetching stock data for weekly performance...")
    stock_section, stock_data = _fetch_stock_data()

    # Add chart embed instructions if we have chart URLs
    chart_instructions = ""
    if stock_data:
        combined_chart = stock_data.get("_combined_chart_url", "")
        if combined_chart:
            chart_instructions += (
                f'\nIMPORTANT: Embed this combined 6-month chart at the TOP of the '
                f'Valve Industry Stocks section:\n'
                f'<img src="{combined_chart}" '
                f'alt="6-Month Valve Industry Stock Performance" '
                f'style="max-width:100%;height:auto;">\n'
            )
        for ticker, data in stock_data.items():
            if isinstance(data, dict) and data.get("chart_url"):
                chart_instructions += (
                    f'For {ticker}, embed: <img src="{data["chart_url"]}" '
                    f'alt="{ticker} 6-Month Chart" style="max-width:100%;height:auto;">\n'
                )

    stock_section_with_charts = stock_section
    if chart_instructions:
        stock_section_with_charts += "\n\n## Chart Embed Instructions\n" + chart_instructions

    logger.info("Fetching trial updates for weekly summary...")
    trials_section = _fetch_trial_updates()

    private_companies = ", ".join(config.PRIVATE_COMPANIES)

    prompt = WEEKLY_PROMPT.format(
        start_date=start_date.strftime("%B %d"),
        end_date=end_date.strftime("%B %d, %Y"),
        digests_section=digests_section,
        weekend_section=weekend_section,
        stock_section=stock_section_with_charts,
        trials_section=trials_section,
        private_companies=private_companies,
    )

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    logger.info(
        f"Generating weekly summary from {len(digests)} daily digests "
        f"({start_date} to {end_date}) with claude-opus-4-6"
    )

    # Inject guidelines knowledge into the system prompt
    from knowledge import get_full_knowledge_context
    knowledge = get_full_knowledge_context()
    system_with_knowledge = SYSTEM_PROMPT
    if knowledge:
        system_with_knowledge += "\n\n" + knowledge
        logger.info(f"Injected {len(knowledge)} chars of guidelines context")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16384,
        system=system_with_knowledge,
        messages=[{"role": "user", "content": prompt}],
        timeout=21600.0,
    )

    summary = message.content[0].text
    logger.info(
        f"Weekly digest generated: {len(summary)} chars, "
        f"tokens: {message.usage.input_tokens} in / {message.usage.output_tokens} out"
    )

    return summary, stock_data


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
