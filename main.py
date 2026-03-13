#!/usr/bin/env python3
"""TAVR Daily Digest Agent - monitors PubMed, news, regulatory, trials, and stocks."""

import logging
import sys
import time

import requests
import smtplib

import config
from sources import pubmed, news, regulatory, trials, stocks
from processing.dedup import DedupDB
from processing.summarizer import create_digest, build_fallback_digest
from delivery.emailer import send_digest
from delivery.substack import export_substack

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("tavr-digest")


def run_daily_digest():
    logger.info("=== TAVR Daily Digest starting ===")

    # 1. Collect from all sources (isolated error handling)
    pubmed_articles = []
    news_articles = []
    regulatory_articles = []
    trial_updates = []
    stock_data = {}

    try:
        pubmed_articles = pubmed.fetch_recent()
        logger.info(f"PubMed: fetched {len(pubmed_articles)} articles")
    except requests.RequestException as e:
        logger.error(f"PubMed fetch failed: {e}")
    except Exception as e:
        logger.error(f"PubMed unexpected error: {e}", exc_info=True)

    try:
        news_articles = news.fetch_recent()
        logger.info(f"News: fetched {len(news_articles)} articles")
    except requests.RequestException as e:
        logger.error(f"News fetch failed: {e}")
    except Exception as e:
        logger.error(f"News unexpected error: {e}", exc_info=True)

    try:
        regulatory_articles = regulatory.fetch_fda_feeds()
        logger.info(f"Regulatory: fetched {len(regulatory_articles)} items")
    except Exception as e:
        logger.error(f"Regulatory fetch failed: {e}", exc_info=True)

    try:
        trial_updates = trials.fetch_trial_updates()
        logger.info(f"Trials: fetched {len(trial_updates)} updates")
    except Exception as e:
        logger.error(f"Trials fetch failed: {e}", exc_info=True)

    try:
        stock_data = stocks.fetch_stock_data()
        logger.info(f"Stocks: fetched data for {len(stock_data)} tickers")
    except Exception as e:
        logger.error(f"Stock data fetch failed: {e}", exc_info=True)

    # Check if we have any article content at all
    total_articles = len(pubmed_articles) + len(news_articles) + len(regulatory_articles)
    if total_articles == 0 and not trial_updates and not stock_data:
        logger.warning("No content retrieved from any source. Exiting.")
        return

    # 2. Deduplicate articles
    db = DedupDB(config.DEDUP_DB_PATH)
    new_pubmed = db.filter_new(pubmed_articles, source="pubmed")
    new_news = db.filter_new(news_articles, source="news")
    new_regulatory = db.filter_new(regulatory_articles, source="regulatory")

    # Always include stock data and trials (not deduped - they're live data)
    has_new_articles = new_pubmed or new_news or new_regulatory
    has_supplemental = trial_updates or stock_data

    if not has_new_articles and not has_supplemental:
        logger.info("No new articles or data since last run. Done.")
        return

    logger.info(
        f"New: {len(new_pubmed)} PubMed, {len(new_news)} news, "
        f"{len(new_regulatory)} regulatory, {len(trial_updates)} trials, "
        f"{len(stock_data)} stocks"
    )

    # 3. Summarize with Claude (retry once on failure)
    digest_content = None
    for attempt in range(2):
        try:
            digest_content = create_digest(
                new_pubmed, new_news, new_regulatory, stock_data, trial_updates,
            )
            break
        except Exception as e:
            logger.warning(f"Claude API attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                time.sleep(30)

    if digest_content is None:
        logger.error("Claude API unavailable. Using fallback digest.")
        digest_content = build_fallback_digest(
            new_pubmed, new_news, new_regulatory, stock_data, trial_updates,
        )

    # 4. Export Substack copy page
    try:
        substack_files = export_substack(
            digest_content, new_pubmed, new_news,
            new_regulatory, stock_data, trial_updates,
        )
        logger.info(f"Substack copy page: {substack_files['copy_page']}")
    except Exception as e:
        logger.error(f"Substack export failed: {e}", exc_info=True)

    # 5. Send email (retry once on failure)
    email_sent = False
    for attempt in range(2):
        try:
            send_digest(
                digest_content, new_pubmed, new_news,
                new_regulatory, stock_data, trial_updates,
            )
            email_sent = True
            break
        except smtplib.SMTPException as e:
            logger.error(f"Email attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                time.sleep(10)
        except Exception as e:
            logger.error(f"Email unexpected error: {e}", exc_info=True)
            break

    if not email_sent:
        logger.critical("Email delivery failed. Articles NOT marked as seen (will retry next run).")
        return

    # 6. Mark articles as seen (only after successful email)
    all_new_articles = new_pubmed + new_news + new_regulatory
    db.mark_seen(all_new_articles)

    # 7. Periodic cleanup
    db.cleanup(days=90)

    logger.info(f"=== TAVR Daily Digest complete: {len(all_new_articles)} articles processed ===")


if __name__ == "__main__":
    try:
        run_daily_digest()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.critical(f"Unhandled error: {e}", exc_info=True)
        sys.exit(1)
