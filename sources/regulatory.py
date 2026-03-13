from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser

import config

logger = logging.getLogger(__name__)


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _is_tavr_relevant(title: str, summary: str) -> bool:
    """Check if an FDA entry is relevant to TAVR/structural heart."""
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in config.FDA_FILTER_KEYWORDS)


def fetch_fda_feeds(days: int = None) -> list[dict]:
    """Fetch and filter FDA RSS feeds for TAVR-relevant entries."""
    days = days or config.LOOKBACK_DAYS
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days + 1)
    articles = []
    seen_ids = set()

    for feed_info in config.FDA_RSS_FEEDS:
        url = feed_info["url"]
        label = feed_info["label"]
        logger.debug(f"Fetching FDA RSS: {label}")

        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.warning(f"Failed to parse FDA feed '{label}': {e}")
            continue

        for entry in feed.entries:
            title = _strip_html(entry.get("title", ""))
            link = entry.get("link", "")
            summary = _strip_html(entry.get("summary", ""))

            if not title or not link:
                continue

            # Filter for TAVR relevance
            if not _is_tavr_relevant(title, summary):
                continue

            # Date filter
            published_parsed = entry.get("published_parsed")
            if published_parsed:
                pub_dt = datetime.fromtimestamp(mktime(published_parsed), tz=timezone.utc)
                if pub_dt < cutoff:
                    continue
                pub_date = pub_dt.strftime("%Y-%m-%d")
            else:
                pub_date = ""

            aid = _article_id(link)
            if aid in seen_ids:
                continue
            seen_ids.add(aid)

            articles.append({
                "id": aid,
                "title": title,
                "snippet": summary[:500],
                "source_name": label,
                "pub_date": pub_date,
                "url": link,
                "source": "regulatory",
            })

    logger.info(f"FDA: retrieved {len(articles)} TAVR-relevant regulatory items")
    return articles
