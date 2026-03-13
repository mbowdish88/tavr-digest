"""Fetch financial news, SEC filings, and market analysis for valve companies."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import date, datetime, timedelta, timezone
from time import mktime
from urllib.parse import quote_plus

import feedparser
import requests

import config

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
SEC_FILING_SEARCH = "https://efts.sec.gov/LATEST/search-index"
SEC_FILING_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _fetch_sec_filings(days: int) -> list[dict]:
    """Fetch recent 8-K filings from SEC EDGAR for tracked companies."""
    articles = []
    end_date = date.today()
    start_date = end_date - timedelta(days=max(days, 7))

    for company, cik in config.SEC_EDGAR_COMPANIES.items():
        try:
            url = "https://efts.sec.gov/LATEST/search-index"
            params = {
                "q": f'"{company}"',
                "dateRange": "custom",
                "startdt": start_date.strftime("%Y-%m-%d"),
                "enddt": end_date.strftime("%Y-%m-%d"),
                "forms": "8-K,8-K/A",
            }
            headers = {"User-Agent": config.SEC_USER_AGENT}

            resp = requests.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for hit in data.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                filing_date = source.get("file_date", "")
                form_type = source.get("form_type", "")
                entity = source.get("entity_name", company)
                file_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K"

                articles.append({
                    "id": _article_id(f"{cik}-{filing_date}-{form_type}"),
                    "title": f"{entity}: {form_type} Filing",
                    "snippet": f"SEC {form_type} filing by {entity} on {filing_date}",
                    "source_name": "SEC EDGAR",
                    "pub_date": filing_date,
                    "url": file_url,
                    "source": "financial",
                })

        except Exception as e:
            logger.debug(f"SEC EDGAR fetch for {company} failed: {e}")

    return articles


def _fetch_financial_news(days: int) -> list[dict]:
    """Fetch financial/M&A/regulatory news via Google News RSS."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days + 1)
    articles = []
    seen_ids: set = set()

    for term in config.FINANCIAL_NEWS_TERMS:
        url = GOOGLE_NEWS_RSS.format(query=quote_plus(term))

        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.debug(f"Financial news RSS failed for '{term}': {e}")
            continue

        for entry in feed.entries:
            title = _strip_html(entry.get("title", ""))
            link = entry.get("link", "")
            snippet = _strip_html(entry.get("summary", ""))

            source_info = entry.get("source", {})
            source_name = source_info.get("title", "") if isinstance(source_info, dict) else ""

            if not title or not link:
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

            aid = _article_id(link)
            if aid in seen_ids:
                continue
            seen_ids.add(aid)

            articles.append({
                "id": aid,
                "title": title,
                "snippet": snippet,
                "source_name": source_name or "Financial News",
                "pub_date": pub_dt.strftime("%Y-%m-%d") if pub_dt else "",
                "url": link,
                "source": "financial",
            })

        if len(articles) >= 20:
            break

    return articles


def _fetch_stock_news() -> list[dict]:
    """Fetch recent news for tracked tickers via yfinance."""
    articles = []

    try:
        import yfinance as yf
    except ImportError:
        return articles

    for ticker in config.STOCK_TICKERS:
        try:
            stock = yf.Ticker(ticker)
            news = getattr(stock, "news", None)
            if not news:
                continue

            for item in news[:3]:
                title = item.get("title", "")
                link = item.get("link", "")
                publisher = item.get("publisher", "")

                if not title or not link:
                    continue

                pub_ts = item.get("providerPublishTime")
                pub_date = ""
                if pub_ts:
                    pub_date = datetime.fromtimestamp(pub_ts, tz=timezone.utc).strftime("%Y-%m-%d")

                aid = _article_id(link)
                articles.append({
                    "id": aid,
                    "title": title,
                    "snippet": "",
                    "source_name": publisher,
                    "pub_date": pub_date,
                    "url": link,
                    "source": "financial",
                })

        except Exception as e:
            logger.debug(f"yfinance news for {ticker} failed: {e}")

    return articles


def fetch_financial_news(days: int = None) -> list[dict]:
    days = days or config.LOOKBACK_DAYS
    all_articles = []
    seen_ids: set = set()

    # SEC filings
    try:
        sec = _fetch_sec_filings(days)
        logger.info(f"SEC EDGAR: found {len(sec)} filings")
        all_articles.extend(sec)
    except Exception as e:
        logger.debug(f"SEC EDGAR failed: {e}")

    # Financial news RSS
    try:
        news = _fetch_financial_news(days)
        logger.info(f"Financial news: found {len(news)} articles")
        all_articles.extend(news)
    except Exception as e:
        logger.debug(f"Financial news RSS failed: {e}")

    # Stock-specific news from yfinance
    try:
        stock_news = _fetch_stock_news()
        logger.info(f"Stock news: found {len(stock_news)} articles")
        all_articles.extend(stock_news)
    except Exception as e:
        logger.debug(f"Stock news failed: {e}")

    # Deduplicate
    unique = []
    for a in all_articles:
        if a["id"] not in seen_ids:
            seen_ids.add(a["id"])
            unique.append(a)

    logger.info(f"Financial: retrieved {len(unique)} total items")
    return unique
