"""Fetch recent valve-relevant articles from major journal RSS feeds."""

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


def _is_relevant(title: str, summary: str) -> bool:
    combined = (title + " " + summary).lower()
    return any(term.lower() in combined for term in config.SEARCH_TERMS)


def fetch_recent(days: int = None) -> list[dict]:
    days = days or config.LOOKBACK_DAYS
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days + 1)
    seen_ids: set = set()
    articles: list[dict] = []

    for feed_info in config.JOURNAL_RSS_FEEDS:
        url = feed_info["url"]
        label = feed_info["label"]

        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.warning(f"Failed to parse journal feed '{label}': {e}")
            continue

        if feed.bozo and not feed.entries:
            logger.warning(f"Journal feed '{label}' returned no entries (bozo={feed.bozo})")
            continue

        count = 0
        for entry in feed.entries:
            title = _strip_html(entry.get("title", ""))
            link = entry.get("link", "")
            summary = _strip_html(entry.get("summary", entry.get("description", "")))

            if not title or not link:
                continue

            if not _is_relevant(title, summary):
                continue

            # Date filter
            published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            if published_parsed:
                try:
                    pub_dt = datetime.fromtimestamp(mktime(published_parsed), tz=timezone.utc)
                except (ValueError, OverflowError):
                    pub_dt = None
            else:
                pub_dt = None

            if pub_dt and pub_dt < cutoff:
                continue

            aid = _article_id(link)
            if aid in seen_ids:
                continue
            seen_ids.add(aid)

            # Extract authors if available
            authors = ""
            if hasattr(entry, "authors") and entry.authors:
                author_names = [a.get("name", "") for a in entry.authors if a.get("name")]
                if author_names:
                    authors = ", ".join(author_names[:5])
                    if len(author_names) > 5:
                        authors += " et al."

            articles.append({
                "id": aid,
                "title": title,
                "abstract": summary[:1000] if summary else "",
                "authors": authors,
                "journal": label,
                "pub_date": pub_dt.strftime("%Y-%m-%d") if pub_dt else "",
                "url": link,
                "source": "journal",
            })
            count += 1

        if count > 0:
            logger.info(f"Journal '{label}': found {count} relevant articles")

    logger.info(f"Journals: retrieved {len(articles)} total relevant articles")
    return articles
