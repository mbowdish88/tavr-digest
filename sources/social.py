"""Monitor social media for valve-related posts via free RSS bridges."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser

import config

logger = logging.getLogger(__name__)

# Nitter instances that provide RSS feeds for Twitter/X accounts (free)
NITTER_INSTANCES = [
    "nitter.privacydev.net",
    "nitter.poast.org",
    "nitter.net",
    "nitter.cz",
    "nitter.1d4.us",
]


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _is_relevant(text: str) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in config.SEARCH_TERMS)


def _try_nitter_feed(handle: str, cutoff: datetime) -> list[dict]:
    """Try fetching a Twitter account's feed via Nitter RSS instances.
    Tries only the first 2 responsive instances to avoid long timeouts."""
    for instance in NITTER_INSTANCES[:2]:
        url = f"https://{instance}/{handle}/rss"
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                continue
            if not feed.entries:
                continue

            posts = []
            for entry in feed.entries:
                text = _strip_html(entry.get("title", "") or entry.get("summary", ""))
                link = entry.get("link", "")

                if not text or not _is_relevant(text):
                    continue

                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    try:
                        pub_dt = datetime.fromtimestamp(mktime(published_parsed), tz=timezone.utc)
                    except (ValueError, OverflowError):
                        pub_dt = None
                else:
                    pub_dt = None

                if pub_dt and pub_dt < cutoff:
                    continue

                # Convert nitter URL back to twitter URL
                twitter_url = link.replace(f"https://{instance}/", "https://x.com/") if link else ""

                posts.append({
                    "id": _article_id(twitter_url or text),
                    "title": text[:200] + ("..." if len(text) > 200 else ""),
                    "snippet": text,
                    "source_name": f"@{handle}",
                    "pub_date": pub_dt.strftime("%Y-%m-%d") if pub_dt else "",
                    "url": twitter_url,
                    "source": "social",
                })

            return posts

        except Exception:
            continue

    return []


def fetch_recent(days: int = None) -> list[dict]:
    days = days or config.LOOKBACK_DAYS
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days + 1)
    all_posts: list[dict] = []
    seen_ids: set = set()

    for account in config.SOCIAL_MEDIA_ACCOUNTS:
        handle = account["handle"]
        label = account["label"]

        try:
            posts = _try_nitter_feed(handle, cutoff)
            for post in posts:
                if post["id"] not in seen_ids:
                    seen_ids.add(post["id"])
                    all_posts.append(post)
            if posts:
                logger.info(f"Social @{handle} ({label}): {len(posts)} relevant posts")
        except Exception as e:
            logger.debug(f"Social @{handle} failed: {e}")

    if not all_posts:
        logger.info("Social: no posts retrieved (Nitter instances may be unavailable)")
    else:
        logger.info(f"Social: retrieved {len(all_posts)} total posts")

    return all_posts
