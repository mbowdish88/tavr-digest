"""Publish The Valve Wire digest to Beehiiv via API."""

import logging
from datetime import date

import requests

import config

logger = logging.getLogger(__name__)

BEEHIIV_API_BASE = "https://api.beehiiv.com/v2"


def _build_subtitle(
    pubmed_articles: list,
    news_articles: list,
    preprint_articles: list = None,
    journal_articles: list = None,
    regulatory_articles: list = None,
    trials: list = None,
) -> str:
    parts = []
    total_research = len(pubmed_articles) + len(preprint_articles or []) + len(journal_articles or [])
    if total_research:
        parts.append(f"{total_research} research article{'s' if total_research != 1 else ''}")
    if news_articles:
        parts.append(f"{len(news_articles)} news item{'s' if len(news_articles) != 1 else ''}")
    if regulatory_articles:
        parts.append(f"{len(regulatory_articles)} regulatory update{'s' if len(regulatory_articles) != 1 else ''}")
    if trials:
        parts.append(f"{len(trials)} trial update{'s' if len(trials) != 1 else ''}")
    return " | ".join(parts) if parts else "Daily valve technology digest"


def publish_to_beehiiv(
    digest_html: str,
    pubmed_articles: list,
    news_articles: list,
    regulatory_articles: list = None,
    stock_data: dict = None,
    trials: list = None,
    preprint_articles: list = None,
    journal_articles: list = None,
    social_posts: list = None,
    financial_news: list = None,
) -> dict:
    if not config.BEEHIIV_API_KEY or not config.BEEHIIV_PUB_ID:
        logger.warning("Beehiiv API key or publication ID not configured. Skipping.")
        return {}

    today = date.today()
    title = f"The Valve Wire - {today.strftime('%B %d, %Y')}"
    subtitle = _build_subtitle(
        pubmed_articles, news_articles,
        preprint_articles, journal_articles,
        regulatory_articles, trials,
    )

    # Build the full post HTML content
    content_parts = [digest_html]

    # Append source links
    all_research = (pubmed_articles or []) + (preprint_articles or []) + (journal_articles or [])
    if all_research:
        content_parts.append("<h2>Research Sources</h2><ul>")
        for a in all_research:
            journal_info = f" &mdash; {a.get('journal', '')}" if a.get('journal') else ""
            content_parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a>{journal_info}</li>'
            )
        content_parts.append("</ul>")

    if news_articles:
        content_parts.append("<h2>News Sources</h2><ul>")
        for a in news_articles:
            content_parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a> &mdash; {a.get("source_name", "")}</li>'
            )
        content_parts.append("</ul>")

    content_parts.append(
        '<hr>'
        '<p style="font-size:14px;color:#1a3a5c;font-weight:600;font-family:Georgia,serif;">'
        'The Valve Wire</p>'
        '<p style="font-size:12px;color:#8a8580;">'
        'By E. Nolan Beckett &middot; '
        '<a href="mailto:nolan.beckett@pm.me" style="color:#2b6cb0;">nolan.beckett@pm.me</a></p>'
        '<p style="font-size:11px;color:#a8a29e;">'
        'AI-synthesized from PubMed, bioRxiv, medRxiv, major cardiology journals, '
        'Google News, FDA, ClinicalTrials.gov, SEC EDGAR, Yahoo Finance.</p>'
    )

    content_html = "\n".join(content_parts)

    url = f"{BEEHIIV_API_BASE}/publications/{config.BEEHIIV_PUB_ID}/posts"
    headers = {
        "Authorization": f"Bearer {config.BEEHIIV_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "title": title,
        "subtitle": subtitle,
        "content_html": content_html,
        "status": "confirmed",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    result = resp.json().get("data", {})

    post_id = result.get("id", "unknown")
    post_url = result.get("web_url", "")
    logger.info(f"Beehiiv: published post {post_id} - {post_url}")

    return result
