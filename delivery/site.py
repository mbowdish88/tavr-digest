"""Publish digests to docs/ for GitHub Pages."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import config

logger = logging.getLogger(__name__)

DOCS_DIR = config.BASE_DIR / "docs"
DIGEST_DIR = DOCS_DIR / "digest"
WEEKLY_DIR = DOCS_DIR / "weekly"


def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
        autoescape=False,
    )


def publish_daily_to_site(
    digest_html: str,
    pubmed_articles: list,
    news_articles: list,
    regulatory_articles: list,
    stock_data: dict,
    trial_updates: list,
    preprint_articles: list,
    journal_articles: list,
    social_posts: list,
    financial_news: list,
) -> Path | None:
    """Render daily digest to docs/digest/YYYY-MM-DD/index.html."""
    today = date.today()
    date_str = today.isoformat()
    out_dir = DIGEST_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    env = _get_env()
    template = env.get_template("digest.html")

    all_research = pubmed_articles + preprint_articles + journal_articles
    html = template.render(
        date=today.strftime("%B %d, %Y"),
        research_count=len(all_research),
        pubmed_count=len(pubmed_articles),
        preprint_count=len(preprint_articles),
        journal_count=len(journal_articles),
        news_count=len(news_articles),
        regulatory_count=len(regulatory_articles),
        trials_count=len(trial_updates),
        digest_html=digest_html,
        pubmed_articles=pubmed_articles,
        preprint_articles=preprint_articles,
        journal_articles=journal_articles,
        news_articles=news_articles,
        regulatory_articles=regulatory_articles,
        trials=trial_updates,
    )

    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    logger.info(f"Site: daily digest published to {out_path}")

    # Rebuild the site index
    _rebuild_index()

    return out_path


def publish_weekly_to_site(weekly_html: str) -> Path | None:
    """Render weekly digest to docs/weekly/YYYY-MM-DD/index.html."""
    today = date.today()
    date_str = today.isoformat()
    out_dir = WEEKLY_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    env = _get_env()
    template = env.get_template("digest.html")

    start = today - timedelta(days=6)
    html = template.render(
        date=f"Week of {start.strftime('%B %d')} - {today.strftime('%B %d, %Y')}",
        research_count="Weekly",
        news_count="Summary",
        regulatory_count=0,
        trials_count=0,
        digest_html=weekly_html,
        pubmed_articles=[],
        preprint_articles=[],
        journal_articles=[],
        news_articles=[],
        regulatory_articles=[],
        trials=[],
    )

    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    logger.info(f"Site: weekly digest published to {out_path}")

    _rebuild_index()

    return out_path


def _rebuild_index():
    """Rebuild docs/index.html with links to all digests."""
    daily_dates = sorted(
        [d.name for d in DIGEST_DIR.iterdir() if d.is_dir() and (d / "index.html").exists()],
        reverse=True,
    ) if DIGEST_DIR.exists() else []

    weekly_dates = sorted(
        [d.name for d in WEEKLY_DIR.iterdir() if d.is_dir() and (d / "index.html").exists()],
        reverse=True,
    ) if WEEKLY_DIR.exists() else []

    env = _get_env()
    template = env.get_template("site_index.html")
    html = template.render(
        daily_dates=daily_dates,
        weekly_dates=weekly_dates,
    )

    index_path = DOCS_DIR / "index.html"
    index_path.write_text(html, encoding="utf-8")
    logger.info(f"Site: index rebuilt with {len(daily_dates)} daily, {len(weekly_dates)} weekly")
