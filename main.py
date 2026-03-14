#!/usr/bin/env python3
"""The Valve Wire - daily transcatheter valve technology digest."""

import logging
import sys
import time
from datetime import date, timedelta

import requests
import smtplib

import config
from sources import pubmed, news, regulatory, trials, stocks, preprints, journals, social, financial
from processing.dedup import DedupDB
from processing.summarizer import create_digest, build_fallback_digest
from processing.weekly import save_daily_digest, create_weekly_digest, clear_week_digests, get_week_digests
from podcast.scriptwriter import generate_podcast_script
from podcast.synthesizer import synthesize_segments
from podcast.assembler import assemble_podcast
from podcast.publisher import publish_podcast
from delivery.emailer import send_digest
from delivery.beehiiv import publish_to_beehiiv

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("valve-wire")


def run_daily_digest():
    logger.info("=== The Valve Wire starting ===")

    # 1. Collect from all sources (isolated error handling)
    pubmed_articles = []
    news_articles = []
    regulatory_articles = []
    trial_updates = []
    stock_data = {}
    preprint_articles = []
    journal_articles = []
    social_posts = []
    financial_news = []

    try:
        pubmed_articles = pubmed.fetch_recent()
        logger.info(f"PubMed: fetched {len(pubmed_articles)} articles")
    except requests.RequestException as e:
        logger.error(f"PubMed fetch failed: {e}")
    except Exception as e:
        logger.error(f"PubMed unexpected error: {e}", exc_info=True)

    # Dedicated clinical trial publications from PubMed
    pubmed_trial_articles = []
    try:
        pubmed_trial_articles = pubmed.fetch_recent(
            query=config.PUBMED_CLINICAL_TRIAL_QUERY, max_results=20
        )
        logger.info(f"PubMed Clinical Trials: fetched {len(pubmed_trial_articles)} articles")
    except Exception as e:
        logger.error(f"PubMed Clinical Trials fetch failed: {e}", exc_info=True)

    try:
        preprint_articles = preprints.fetch_recent()
        logger.info(f"Preprints: fetched {len(preprint_articles)} articles")
    except Exception as e:
        logger.error(f"Preprints fetch failed: {e}", exc_info=True)

    try:
        journal_articles = journals.fetch_recent()
        logger.info(f"Journals: fetched {len(journal_articles)} articles")
    except Exception as e:
        logger.error(f"Journals fetch failed: {e}", exc_info=True)

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

    # Landmark trial status monitoring
    landmark_updates = []
    try:
        landmark_updates = trials.fetch_landmark_trials()
        logger.info(f"Landmark Trials: fetched {len(landmark_updates)} updates")
    except Exception as e:
        logger.error(f"Landmark trials fetch failed: {e}", exc_info=True)

    try:
        stock_data = stocks.fetch_stock_data()
        logger.info(f"Stocks: fetched data for {len(stock_data)} tickers")
    except Exception as e:
        logger.error(f"Stock data fetch failed: {e}", exc_info=True)

    try:
        social_posts = social.fetch_recent()
        logger.info(f"Social: fetched {len(social_posts)} posts")
    except Exception as e:
        logger.error(f"Social fetch failed: {e}", exc_info=True)

    try:
        financial_news = financial.fetch_financial_news()
        logger.info(f"Financial: fetched {len(financial_news)} items")
    except Exception as e:
        logger.error(f"Financial fetch failed: {e}", exc_info=True)

    # Merge clinical trial PubMed articles into main PubMed list (deduped by URL)
    seen_urls = {a.get("url") for a in pubmed_articles}
    for a in pubmed_trial_articles:
        if a.get("url") not in seen_urls:
            a["source"] = "pubmed_clinical_trial"
            pubmed_articles.append(a)
            seen_urls.add(a.get("url"))

    # Merge landmark trials into trial updates (deduped by NCT ID)
    seen_ncts = {t.get("nct_id") for t in trial_updates}
    for t in landmark_updates:
        if t.get("nct_id") not in seen_ncts:
            trial_updates.append(t)

    # Check if we have any content at all
    total_articles = (
        len(pubmed_articles) + len(news_articles) + len(regulatory_articles)
        + len(preprint_articles) + len(journal_articles)
    )
    if total_articles == 0 and not trial_updates and not stock_data and not financial_news:
        logger.warning("No content retrieved from any source. Exiting.")
        return

    # 2. Deduplicate articles
    db = DedupDB(config.DEDUP_DB_PATH)
    new_pubmed = db.filter_new(pubmed_articles, source="pubmed")
    new_news = db.filter_new(news_articles, source="news")
    new_regulatory = db.filter_new(regulatory_articles, source="regulatory")
    new_preprints = db.filter_new(preprint_articles, source="preprint")
    new_journals = db.filter_new(journal_articles, source="journal")
    new_social = db.filter_new(social_posts, source="social")
    new_financial = db.filter_new(financial_news, source="financial")

    # Always include stock data and trials (not deduped - they're live data)
    has_new_articles = (
        new_pubmed or new_news or new_regulatory
        or new_preprints or new_journals or new_social or new_financial
    )
    has_supplemental = trial_updates or stock_data

    if not has_new_articles and not has_supplemental:
        logger.info("No new articles or data since last run. Done.")
        return

    logger.info(
        f"New: {len(new_pubmed)} PubMed, {len(new_preprints)} preprints, "
        f"{len(new_journals)} journals, {len(new_news)} news, "
        f"{len(new_regulatory)} regulatory, {len(trial_updates)} trials "
        f"({len(landmark_updates)} landmark), "
        f"{len(stock_data)} stocks, {len(new_social)} social, "
        f"{len(new_financial)} financial"
    )

    # 3. Summarize with Claude (retry once on failure)
    digest_content = None
    for attempt in range(2):
        try:
            digest_content = create_digest(
                new_pubmed, new_news, new_regulatory, stock_data, trial_updates,
                new_preprints, new_journals, new_social, new_financial,
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
            new_preprints, new_journals, new_social, new_financial,
        )

    # 4. Save daily digest for weekly compilation
    save_daily_digest(digest_content)

    # 5. Publish to Beehiiv
    try:
        beehiiv_result = publish_to_beehiiv(
            digest_content, new_pubmed, new_news, new_regulatory,
            stock_data, trial_updates, new_preprints, new_journals,
            new_social, new_financial,
        )
        if beehiiv_result:
            logger.info(f"Beehiiv: published post {beehiiv_result.get('id', 'unknown')}")
    except Exception as e:
        logger.error(f"Beehiiv publish failed: {e}", exc_info=True)

    # 6. Send email (retry once on failure)
    email_sent = False
    for attempt in range(2):
        try:
            send_digest(
                digest_content, new_pubmed, new_news,
                new_regulatory, stock_data, trial_updates,
                new_preprints, new_journals, new_social, new_financial,
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

    # 7. Mark articles as seen (only after successful email)
    all_new_articles = (
        new_pubmed + new_news + new_regulatory
        + new_preprints + new_journals + new_social + new_financial
    )
    db.mark_seen(all_new_articles)

    # 8. Periodic cleanup
    db.cleanup(days=90)

    logger.info(f"=== The Valve Wire complete: {len(all_new_articles)} articles processed ===")


US_HOLIDAYS = {
    # Fixed-date holidays (month, day)
    (1, 1),   # New Year's Day
    (6, 19),  # Juneteenth
    (7, 4),   # Independence Day
    (11, 11), # Veterans Day
    (12, 25), # Christmas Day
}

# Floating holidays are computed per year
def _floating_holidays(year: int) -> set:
    """Compute floating US federal holidays for a given year."""
    from datetime import timedelta
    holidays = set()

    # MLK Day: 3rd Monday of January
    jan1 = date(year, 1, 1)
    first_monday = jan1 + timedelta(days=(7 - jan1.weekday()) % 7)
    holidays.add(first_monday + timedelta(weeks=2))

    # Presidents' Day: 3rd Monday of February
    feb1 = date(year, 2, 1)
    first_monday = feb1 + timedelta(days=(7 - feb1.weekday()) % 7)
    holidays.add(first_monday + timedelta(weeks=2))

    # Memorial Day: last Monday of May
    may31 = date(year, 5, 31)
    holidays.add(may31 - timedelta(days=(may31.weekday()) % 7))

    # Labor Day: 1st Monday of September
    sep1 = date(year, 9, 1)
    first_monday = sep1 + timedelta(days=(7 - sep1.weekday()) % 7)
    holidays.add(first_monday)

    # Columbus Day: 2nd Monday of October
    oct1 = date(year, 10, 1)
    first_monday = oct1 + timedelta(days=(7 - oct1.weekday()) % 7)
    holidays.add(first_monday + timedelta(weeks=1))

    # Thanksgiving: 4th Thursday of November
    nov1 = date(year, 11, 1)
    first_thursday = nov1 + timedelta(days=(3 - nov1.weekday()) % 7)
    holidays.add(first_thursday + timedelta(weeks=3))

    return holidays


def is_publish_day() -> bool:
    """Return False on weekends and major US holidays."""
    today = date.today()

    # Skip weekends
    if today.weekday() >= 5:
        return False

    # Skip fixed holidays
    if (today.month, today.day) in US_HOLIDAYS:
        return False

    # Skip floating holidays
    if today in _floating_holidays(today.year):
        return False

    return True


def run_weekly_summary():
    """Generate and send the weekly summary digest."""
    logger.info("=== The Valve Wire Weekly starting ===")

    weekly_html = create_weekly_digest()
    if not weekly_html:
        logger.warning("No daily digests found. Skipping weekly summary.")
        return

    today = date.today()
    subject = (
        f"The Valve Wire Weekly - Week of {(today - timedelta(days=6)).strftime('%B %d')} "
        f"to {today.strftime('%B %d, %Y')}"
    )

    # Use the email template with weekly content
    from delivery.emailer import _render_html, _html_to_plaintext
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Render using the standard template
    from jinja2 import Environment, FileSystemLoader
    env = Environment(
        loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
        autoescape=False,
    )
    template = env.get_template("digest.html")
    html_body = template.render(
        date=f"Week of {(today - timedelta(days=6)).strftime('%B %d')} - {today.strftime('%B %d, %Y')}",
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

    text_body = _html_to_plaintext(html_body)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = ", ".join(config.EMAIL_TO)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.EMAIL_FROM, config.EMAIL_TO, msg.as_string())
        logger.info(f"Weekly summary sent to {', '.join(config.EMAIL_TO)}")
    except Exception as e:
        logger.error(f"Weekly email failed: {e}", exc_info=True)
        return

    # Clear daily digests after successful send
    clear_week_digests()
    logger.info("=== The Valve Wire Weekly complete ===")


def run_weekly_podcast(weekly_html: str = None):
    """Generate and publish the weekly podcast episode."""
    logger.info("=== The Valve Wire Podcast starting ===")

    today = date.today()
    start = today - timedelta(days=6)
    start_str = start.strftime("%B %d")
    end_str = today.strftime("%B %d, %Y")
    episode_date = today.isoformat()

    # If no weekly HTML provided, try to generate it
    if not weekly_html:
        weekly_html = create_weekly_digest()
        if not weekly_html:
            logger.warning("No weekly content available for podcast.")
            return

    # 1. Generate script
    logger.info("Step 1: Generating podcast script...")
    script = generate_podcast_script(weekly_html, start_str, end_str)
    if not script:
        logger.error("Failed to generate podcast script.")
        return

    # 2. Synthesize voices
    logger.info("Step 2: Synthesizing audio segments...")
    segments = synthesize_segments(script, episode_date)
    successful = sum(1 for s in segments if s.get("audio_path"))
    if successful == 0:
        logger.error("No audio segments synthesized.")
        return

    # 3. Assemble podcast
    logger.info("Step 3: Assembling final podcast...")
    title = f"The Valve Wire Weekly - Week of {start_str} to {end_str}"
    mp3_path = assemble_podcast(segments, episode_date, title)

    # 4. Publish
    logger.info("Step 4: Publishing podcast...")
    episode = publish_podcast(mp3_path, episode_date, weekly_html)

    if episode:
        logger.info(f"=== The Valve Wire Podcast complete: {episode.get('duration', '?')} ===")
    else:
        logger.error("Podcast publish failed.")


DAY_NAMES = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def is_weekly_day() -> bool:
    """Check if today is the weekly publish day (Saturday)."""
    today = date.today()
    publish_weekday = DAY_NAMES.get(config.WEEKLY_PUBLISH_DAY, 5)
    return today.weekday() == publish_weekday


if __name__ == "__main__":
    try:
        # Podcast generation (can run standalone)
        if "--podcast" in sys.argv:
            run_weekly_podcast()
            sys.exit(0)

        # Weekly summary on Saturday
        if is_weekly_day():
            if "--weekly" in sys.argv or "--test-weekly" in sys.argv:
                run_weekly_summary()
            else:
                logger.info(
                    f"Today is {date.today().strftime('%A, %B %d')} — "
                    f"run with --weekly to generate weekly summary."
                )
            if "--test-weekly" not in sys.argv:
                sys.exit(0)

        # Daily digest on weekdays (skip weekends/holidays)
        if not is_publish_day():
            logger.info(
                f"Today is {date.today().strftime('%A, %B %d')} — "
                f"skipping daily digest (weekend or holiday)."
            )
            sys.exit(0)

        run_daily_digest()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.critical(f"Unhandled error: {e}", exc_info=True)
        sys.exit(1)
