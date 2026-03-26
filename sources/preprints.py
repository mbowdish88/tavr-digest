"""Fetch TAVR/structural heart preprints from bioRxiv and medRxiv."""

from __future__ import annotations

import hashlib
import logging
from datetime import date, timedelta

import requests

import config

logger = logging.getLogger(__name__)

BIORXIV_API = "https://api.biorxiv.org/details/{server}/{start}/{end}"


def _article_id(doi: str) -> str:
    return hashlib.sha256(doi.encode()).hexdigest()[:16]


def _is_relevant(title: str, abstract: str) -> bool:
    combined = (title + " " + abstract).lower()
    return any(term.lower() in combined for term in config.SEARCH_TERMS)


def _fetch_server(server: str, start_date: str, end_date: str) -> list[dict]:
    url = BIORXIV_API.format(server=server, start=start_date, end=end_date)
    articles = []
    cursor = 0

    while True:
        try:
            resp = requests.get(f"{url}/{cursor}", timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"{server} API request failed (cursor={cursor}): {e}")
            break

        collection = data.get("collection", [])
        if not collection:
            break

        for item in collection:
            title = item.get("title", "")
            abstract = item.get("abstract", "")

            if not _is_relevant(title, abstract):
                continue

            doi = item.get("doi", "")
            authors = item.get("authors", "")
            if len(authors) > 100:
                authors = authors[:100] + "..."

            articles.append({
                "id": _article_id(doi),
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": server.capitalize(),
                "pub_date": item.get("date", ""),
                "doi": doi,
                "url": f"https://doi.org/{doi}" if doi else "",
                "source": "preprint",
            })

        total = int(data.get("messages", [{}])[0].get("total", 0))
        cursor += len(collection)
        if cursor >= total:
            break

    return articles


def fetch_recent(days: int = None) -> list[dict]:
    days = days or config.LOOKBACK_DAYS
    end = date.today()
    start = end - timedelta(days=days)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    articles = []
    for server in ["medrxiv", "biorxiv"]:
        try:
            results = _fetch_server(server, start_str, end_str)
            logger.info(f"{server}: found {len(results)} relevant preprints")
            articles.extend(results)
        except Exception as e:
            logger.error(f"{server} fetch failed: {e}", exc_info=True)

    logger.info(f"Preprints: retrieved {len(articles)} total")
    return articles
