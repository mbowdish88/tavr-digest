import logging
import re
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

import config

logger = logging.getLogger(__name__)


def _render_html(
    digest_html: str,
    pubmed_articles: list,
    news_articles: list,
    regulatory_articles: list = None,
    stock_data: dict = None,
    trials: list = None,
) -> str:
    regulatory_articles = regulatory_articles or []
    trials = trials or []

    env = Environment(
        loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
        autoescape=False,
    )
    template = env.get_template("digest.html")

    return template.render(
        date=date.today().strftime("%B %d, %Y"),
        pubmed_count=len(pubmed_articles),
        news_count=len(news_articles),
        regulatory_count=len(regulatory_articles),
        trials_count=len(trials),
        digest_html=digest_html,
        pubmed_articles=pubmed_articles,
        news_articles=news_articles,
        regulatory_articles=regulatory_articles,
        trials=trials,
    )


def _html_to_plaintext(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def send_digest(
    digest_html: str,
    pubmed_articles: list,
    news_articles: list,
    regulatory_articles: list = None,
    stock_data: dict = None,
    trials: list = None,
) -> None:
    if not config.EMAIL_TO:
        logger.warning("No EMAIL_TO configured. Skipping email send.")
        return

    total = len(pubmed_articles) + len(news_articles) + len(regulatory_articles or [])
    subject = (
        f"TAVR Digest - {date.today().strftime('%B %d, %Y')} "
        f"({total} article{'s' if total != 1 else ''})"
    )

    html_body = _render_html(
        digest_html, pubmed_articles, news_articles,
        regulatory_articles, stock_data, trials,
    )
    text_body = _html_to_plaintext(html_body)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = ", ".join(config.EMAIL_TO)

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    logger.info(f"Connecting to {config.SMTP_HOST}:{config.SMTP_PORT}")

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.EMAIL_FROM, config.EMAIL_TO, msg.as_string())

    logger.info(f"Digest email sent to {', '.join(config.EMAIL_TO)}")
