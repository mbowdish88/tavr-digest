#!/usr/bin/env python3
"""Simulate a week of daily digests, then generate a weekly summary.

This script:
1. Fetches articles with a 7-day lookback
2. Splits them into daily batches
3. Generates a digest for each day
4. Saves each to data/weekly/
5. Generates the weekly summary
"""

import logging
import sys
from datetime import date, timedelta

import config
from sources import pubmed, news, trials, stocks, financial
from processing.summarizer import create_digest
from processing.weekly import save_daily_digest, create_weekly_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("weekly-test")


def main():
    today = date.today()
    # Simulate Mon-Fri of this past week
    friday = today - timedelta(days=(today.weekday() - 4) % 7)
    if friday > today:
        friday -= timedelta(days=7)
    monday = friday - timedelta(days=4)

    logger.info(f"Simulating daily digests for {monday} to {friday}")

    # Fetch a full week of articles
    logger.info("Fetching week's articles from PubMed (7-day lookback)...")
    articles = pubmed.fetch_recent(days=7, max_results=50)
    logger.info(f"Got {len(articles)} PubMed articles")

    news_articles = []
    try:
        news_articles = news.fetch_recent()
        logger.info(f"Got {len(news_articles)} news articles")
    except Exception as e:
        logger.warning(f"News fetch failed: {e}")

    trial_updates = []
    try:
        trial_updates = trials.fetch_trial_updates(days=7)
        from sources.trials import fetch_landmark_trials
        landmark = fetch_landmark_trials()
        seen = {t["nct_id"] for t in trial_updates}
        for t in landmark:
            if t["nct_id"] not in seen:
                trial_updates.append(t)
        logger.info(f"Got {len(trial_updates)} trial updates")
    except Exception as e:
        logger.warning(f"Trials fetch failed: {e}")

    stock_data = {}
    try:
        stock_data = stocks.fetch_stock_data()
        logger.info(f"Got {len(stock_data)} stock entries")
    except Exception as e:
        logger.warning(f"Stocks fetch failed: {e}")

    financial_news = []
    try:
        financial_news = financial.fetch_financial_news()
        logger.info(f"Got {len(financial_news)} financial items")
    except Exception as e:
        logger.warning(f"Financial fetch failed: {e}")

    # Split articles roughly across 5 days
    days = []
    current = monday
    while current <= friday:
        days.append(current)
        current += timedelta(days=1)

    chunk_size = max(1, len(articles) // len(days))

    for i, day in enumerate(days):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < len(days) - 1 else len(articles)
        day_articles = articles[start_idx:end_idx]

        # Give news/trials/stocks only to relevant days
        day_news = news_articles if i == len(days) - 1 else []
        day_trials = trial_updates if i in [0, len(days) - 1] else []
        day_stocks = stock_data if i == len(days) - 1 else {}
        day_financial = financial_news if i == 2 else []

        logger.info(f"Generating digest for {day.strftime('%A %B %d')} ({len(day_articles)} articles)...")

        try:
            digest = create_digest(
                day_articles, day_news, [], day_stocks, day_trials,
                [], [], [], day_financial,
            )
            save_daily_digest(digest, digest_date=day)
            logger.info(f"Saved digest for {day}")
        except Exception as e:
            logger.error(f"Failed to generate digest for {day}: {e}", exc_info=True)

    # Now generate the weekly summary
    logger.info("=" * 60)
    logger.info("Generating weekly summary...")
    weekly_html = create_weekly_digest(end_date=friday)

    if weekly_html:
        # Save it for review
        output_path = config.DATA_DIR / "weekly_test_output.html"
        output_path.write_text(weekly_html, encoding="utf-8")
        logger.info(f"Weekly summary saved to {output_path}")
        logger.info(f"Weekly summary: {len(weekly_html)} chars")
        print("\n" + "=" * 60)
        print("WEEKLY SUMMARY PREVIEW (first 500 chars):")
        print("=" * 60)
        print(weekly_html[:500])
    else:
        logger.error("Failed to generate weekly summary")


if __name__ == "__main__":
    main()
