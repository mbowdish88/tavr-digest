import logging

from anthropic import Anthropic

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a medical literature analyst specializing in structural heart disease \
and transcatheter aortic valve replacement (TAVR/TAVI). You produce a daily \
newsletter digest for cardiac surgeons and interventional cardiologists. \
The digest is published on Substack, so it should read like a polished, \
engaging newsletter — authoritative but approachable, with clear narrative \
flow between sections."""

DIGEST_PROMPT_TEMPLATE = """\
Produce a daily TAVR newsletter digest from the data below. This will be \
published directly on Substack, so write it as a polished newsletter post.

## Format Rules (Substack compatibility)
- Use ONLY these HTML tags: <h2>, <h3>, <p>, <ul>, <li>, <ol>, <a>, <strong>, \
<em>, <blockquote>, <hr>
- Do NOT use <table>, <div>, <span>, <style>, or any CSS. Substack strips these.
- For stock data or structured comparisons, use bullet lists instead of tables.
- Every section of text should be wrapped in <p> tags.
- Use <hr> between major sections for visual separation.
- Links: <a href="URL">linked text</a>

## Content Instructions
- Open with a compelling 2-3 sentence lead paragraph summarizing the day's most \
important TAVR developments. Write it like a newsletter intro — hook the reader.
- Organize into these sections using <h2> headers (omit empty sections):
  - Today's Key Findings
  - Clinical Research
  - Device & Technology
  - Regulatory & Policy
  - Industry & Market
  - TAVR Industry Stocks
  - Clinical Trial Updates
- For research articles (PubMed), write a brief narrative paragraph noting study \
design, sample size if available, key finding, and clinical relevance. Do not just \
list bullet points — give context and significance.
- For news articles, provide a 1-2 sentence summary with source attribution.
- For regulatory items, highlight what changed and the clinical/reimbursement impact.
- Flag practice-changing or particularly notable findings with <strong>[NOTABLE]</strong>.
- Include hyperlinks to original articles using <a href="URL">linked text</a>.
- End with a brief 1-2 sentence closing thought or look-ahead.
- Tone: expert, concise, clinically focused, but readable as a newsletter. \
Avoid dry academic listing — connect the dots between findings where relevant.

{stock_instructions}

{trials_instructions}

## PubMed Articles ({pubmed_count})
{pubmed_section}

## News Articles ({news_count})
{news_section}

## Regulatory Updates ({regulatory_count})
{regulatory_section}

{stock_data_section}

{trials_data_section}

Produce the Substack-ready HTML digest now."""


def _format_pubmed_articles(articles: list[dict]) -> str:
    if not articles:
        return "None today."

    parts = []
    for a in articles:
        parts.append(
            f"PMID: {a['id']}\n"
            f"Title: {a['title']}\n"
            f"Authors: {a['authors']}\n"
            f"Journal: {a['journal']}, {a['pub_date']}\n"
            f"URL: {a['url']}\n"
            f"Abstract: {a['abstract']}\n"
        )
    return "\n---\n".join(parts)


def _format_news_articles(articles: list[dict]) -> str:
    if not articles:
        return "None today."

    parts = []
    for a in articles:
        parts.append(
            f"Title: {a['title']}\n"
            f"Source: {a.get('source_name', 'Unknown')}\n"
            f"Date: {a['pub_date']}\n"
            f"URL: {a['url']}\n"
            f"Snippet: {a.get('snippet', '')}\n"
        )
    return "\n---\n".join(parts)


def _format_regulatory(articles: list[dict]) -> str:
    if not articles:
        return "None today."

    parts = []
    for a in articles:
        parts.append(
            f"Title: {a['title']}\n"
            f"Source: {a.get('source_name', 'Unknown')}\n"
            f"Date: {a['pub_date']}\n"
            f"URL: {a['url']}\n"
            f"Details: {a.get('snippet', '')}\n"
        )
    return "\n---\n".join(parts)


def _format_stock_data(stock_data: dict) -> str:
    if not stock_data:
        return ""

    parts = ["## TAVR Industry Stock Data"]
    for ticker, data in stock_data.items():
        parts.append(
            f"Ticker: {ticker} ({data['company']})\n"
            f"Close: ${data['close_price']} (date: {data['close_date']})\n"
            f"Daily Change: {data['change']:+.2f} ({data['change_pct']:+.2f}%)\n"
            f"5-Day Range: ${data['low_5d']} - ${data['high_5d']}\n"
            f"Volume: {data['volume']:,}"
        )
        if data.get("target_price"):
            parts.append(
                f"Analyst Target: ${data['target_price']} "
                f"(range: ${data['target_low']} - ${data['target_high']}, "
                f"{data['num_analysts']} analysts)\n"
                f"Recommendation: {data['recommendation']}"
            )
        parts.append("---")

    parts.append(
        "Note: JenaValve Technology and J Valve Technology are private companies "
        "(no public stock data available)."
    )
    return "\n".join(parts)


def _format_trials(trials: list[dict]) -> str:
    if not trials:
        return ""

    parts = ["## Recently Updated Clinical Trials"]
    for t in trials:
        parts.append(
            f"NCT ID: {t['nct_id']}\n"
            f"Title: {t['title']}\n"
            f"Status: {t['status']}\n"
            f"Phase: {t['phase']}\n"
            f"Enrollment: {t['enrollment']}\n"
            f"Sponsor: {t['sponsor']}\n"
            f"Last Updated: {t['last_update']}\n"
            f"Interventions: {t['interventions']}\n"
            f"URL: {t['url']}\n"
        )
        parts.append("---")
    return "\n".join(parts)


def create_digest(
    pubmed_articles: list[dict],
    news_articles: list[dict],
    regulatory_articles: list[dict] = None,
    stock_data: dict = None,
    trials: list[dict] = None,
) -> str:
    regulatory_articles = regulatory_articles or []
    stock_data = stock_data or {}
    trials = trials or []

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Build conditional instruction sections
    stock_instructions = ""
    stock_data_section = ""
    if stock_data:
        stock_instructions = (
            "- Include a <h2>TAVR Industry Stocks</h2> section. "
            "For each ticker, use a bold company name as a subheading, then a bullet list "
            "with closing price, daily change ($ and %), 5-day range, and analyst target. "
            "Do NOT use HTML tables — use <strong> and <ul>/<li> only. "
            "Add a brief 1-2 sentence commentary on any significant moves. "
            "Note that JenaValve and J Valve are private companies."
        )
        stock_data_section = _format_stock_data(stock_data)

    trials_instructions = ""
    trials_data_section = ""
    if trials:
        trials_instructions = (
            "- Include a <h2>Clinical Trial Updates</h2> section. "
            "List each trial with its linked NCT ID, title, status, phase, enrollment, "
            "and sponsor using bullet lists. Group by status if helpful (e.g., newly recruiting, "
            "active, completed). Highlight any trials that changed status. "
            "Do NOT use HTML tables — use <ul>/<li> and <strong> only."
        )
        trials_data_section = _format_trials(trials)

    prompt = DIGEST_PROMPT_TEMPLATE.format(
        pubmed_count=len(pubmed_articles),
        pubmed_section=_format_pubmed_articles(pubmed_articles),
        news_count=len(news_articles),
        news_section=_format_news_articles(news_articles),
        regulatory_count=len(regulatory_articles),
        regulatory_section=_format_regulatory(regulatory_articles),
        stock_instructions=stock_instructions,
        stock_data_section=stock_data_section,
        trials_instructions=trials_instructions,
        trials_data_section=trials_data_section,
    )

    total = len(pubmed_articles) + len(news_articles) + len(regulatory_articles)
    logger.info(
        f"Sending {total} articles + {len(stock_data)} stocks + {len(trials)} trials "
        f"to Claude ({config.CLAUDE_MODEL}) for summarization"
    )

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    digest_html = message.content[0].text
    logger.info(
        f"Digest generated: {len(digest_html)} chars, "
        f"tokens used: {message.usage.input_tokens} in / {message.usage.output_tokens} out"
    )

    return digest_html


def build_fallback_digest(
    pubmed_articles: list[dict],
    news_articles: list[dict],
    regulatory_articles: list[dict] = None,
    stock_data: dict = None,
    trials: list[dict] = None,
) -> str:
    regulatory_articles = regulatory_articles or []
    stock_data = stock_data or {}
    trials = trials or []

    parts = ["<h2>TAVR Daily Digest (AI summary unavailable)</h2>"]

    if pubmed_articles:
        parts.append("<h3>PubMed Articles</h3><ul>")
        for a in pubmed_articles:
            parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a> &mdash; '
                f'{a["journal"]}, {a["pub_date"]}</li>'
            )
        parts.append("</ul>")

    if news_articles:
        parts.append("<h3>News</h3><ul>")
        for a in news_articles:
            parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a> &mdash; '
                f'{a.get("source_name", "")}, {a["pub_date"]}</li>'
            )
        parts.append("</ul>")

    if regulatory_articles:
        parts.append("<h3>Regulatory Updates</h3><ul>")
        for a in regulatory_articles:
            parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a> &mdash; '
                f'{a.get("source_name", "")}, {a["pub_date"]}</li>'
            )
        parts.append("</ul>")

    if stock_data:
        parts.append("<h3>TAVR Industry Stocks</h3><table border='1' cellpadding='5'>")
        parts.append("<tr><th>Ticker</th><th>Company</th><th>Close</th><th>Change</th></tr>")
        for ticker, d in stock_data.items():
            parts.append(
                f'<tr><td>{ticker}</td><td>{d["company"]}</td>'
                f'<td>${d["close_price"]}</td>'
                f'<td>{d["change_pct"]:+.2f}%</td></tr>'
            )
        parts.append("</table>")
        parts.append("<p><em>JenaValve Technology and J Valve Technology are private (no stock data).</em></p>")

    if trials:
        parts.append("<h3>Clinical Trial Updates</h3><ul>")
        for t in trials:
            parts.append(
                f'<li><a href="{t["url"]}">{t["nct_id"]}</a>: {t["title"]} '
                f'&mdash; {t["status"]}, {t["sponsor"]}</li>'
            )
        parts.append("</ul>")

    return "\n".join(parts)
