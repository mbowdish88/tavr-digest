"""Publish digests to docs/ for GitHub Pages."""

from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import config

logger = logging.getLogger(__name__)

DOCS_DIR = config.BASE_DIR / "docs"
DIGEST_DIR = DOCS_DIR / "digest"
WEEKLY_DIR = DOCS_DIR / "weekly"


def _save_chart_images(stock_data: dict, out_dir: Path) -> dict:
    """Save downloaded chart PNGs to out_dir/charts/ and return URL->path map."""
    if not stock_data:
        return {}

    url_map = {}
    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    # Combined chart
    combined_image = stock_data.get("_combined_chart_image")
    combined_url = stock_data.get("_combined_chart_url")
    if combined_image and combined_url:
        path = charts_dir / "combined_6m.png"
        path.write_bytes(combined_image)
        url_map[combined_url] = "charts/combined_6m.png"

    # Individual ticker charts
    for key, value in stock_data.items():
        if not isinstance(value, dict):
            continue
        image = value.get("chart_image")
        chart_url = value.get("chart_url")
        if image and chart_url:
            path = charts_dir / f"{key}_6m.png"
            path.write_bytes(image)
            url_map[chart_url] = f"charts/{key}_6m.png"

    if url_map:
        logger.info(f"Saved {len(url_map)} chart images to {charts_dir}")
    return url_map


def _rewrite_chart_urls(html: str, url_map: dict) -> str:
    """Replace QuickChart URLs with local paths in HTML."""
    for url, local_path in url_map.items():
        html = html.replace(url, local_path)
    return html


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

    # Save chart images and rewrite URLs for persistence
    url_map = _save_chart_images(stock_data, out_dir)
    if url_map:
        html = _rewrite_chart_urls(html, url_map)

    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    logger.info(f"Site: daily digest published to {out_path}")

    # Rebuild the site index
    _rebuild_index()

    return out_path


def publish_weekly_to_site(weekly_html: str, stock_data: dict = None) -> Path | None:
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

    # Save chart images and rewrite URLs for persistence
    if stock_data:
        url_map = _save_chart_images(stock_data, out_dir)
        if url_map:
            html = _rewrite_chart_urls(html, url_map)

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
