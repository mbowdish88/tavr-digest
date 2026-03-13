import logging

from anthropic import Anthropic

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a medical literature and market analyst specializing in structural heart \
disease, including transcatheter aortic (TAVR/TAVI), mitral (MitraClip, PASCAL, TMVR), \
and tricuspid (TriClip, TTVR) valve therapies. You produce a daily newsletter called \
"The Valve Wire" for a broad audience: cardiac surgeons, interventional cardiologists, \
trainees, patients with valvular heart disease, industry stakeholders, and regulatory \
agencies. The digest is published on Beehiiv, so it should read like a polished, \
engaging newsletter — authoritative but approachable, with clear narrative flow."""

DIGEST_PROMPT_TEMPLATE = """\
Produce a daily valve technology newsletter digest from the data below. This will be \
published directly as "The Valve Wire" on Beehiiv.

## Format Rules (Beehiiv/email compatibility)
- Use ONLY these HTML tags: <h2>, <h3>, <p>, <ul>, <li>, <ol>, <a>, <strong>, \
<em>, <blockquote>, <hr>
- Do NOT use <table>, <div>, <span>, <style>, or any CSS. These are stripped.
- For stock data or structured comparisons, use bullet lists instead of tables.
- Every section of text should be wrapped in <p> tags.
- Use <hr> between major sections for visual separation.
- Links: <a href="URL">linked text</a>

## Content Instructions
- Begin with an <h2>Executive Summary</h2> — 3-4 sentences in plain language that \
any reader (including patients) can understand. Summarize the day's most important \
developments across all valve types.

- Then write a more detailed lead paragraph for the clinical audience, hooking the \
reader with the day's key developments.

- Organize into these sections using <h2> headers (omit sections with no content):
  - Executive Summary (always include)
  - Today's Key Findings
  - Aortic Valve (TAVR/TAVI)
  - Mitral Valve (MitraClip, PASCAL, TMVR)
  - Tricuspid Valve (TriClip, TTVR)
  - Surgical vs. Transcatheter Comparisons
  - Preprint Highlights
  - Device & Technology
  - Regulatory & Policy
  - Industry & Market
  - Financial Analysis
  - Valve Industry Stocks
  - Clinical Trial Updates
  - Social & Conference Highlights

- For research articles (PubMed, journals, preprints), write a brief narrative paragraph \
noting study design, sample size if available, key finding, and clinical relevance.
- For news articles, provide a 1-2 sentence summary with source attribution.
- For regulatory items, highlight what changed and the clinical/reimbursement impact.
- For the Financial Analysis section, synthesize SEC filings, M&A activity, reimbursement \
changes, and market trends into a cohesive narrative — not just bullet points.
- For Surgical vs. Transcatheter Comparisons, highlight any studies comparing surgical \
and transcatheter approaches across any valve position.
- Flag practice-changing or particularly notable findings with <strong>[NOTABLE]</strong>.
- Include hyperlinks to original articles using <a href="URL">linked text</a>.
- End with a brief 1-2 sentence closing thought or look-ahead.
- Tone: expert, concise, clinically focused, but readable as a newsletter. \
Avoid dry academic listing — connect the dots between findings where relevant.

{stock_instructions}

{trials_instructions}

## PubMed Articles ({pubmed_count})
{pubmed_section}

## Journal Articles ({journal_count})
{journal_section}

## Preprint Articles ({preprint_count})
{preprint_section}

## News Articles ({news_count})
{news_section}

## Regulatory Updates ({regulatory_count})
{regulatory_section}

{stock_data_section}

{trials_data_section}

{social_section}

{financial_section}

Produce the newsletter-ready HTML digest now."""


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


def _format_journal_articles(articles: list[dict]) -> str:
    if not articles:
        return "None today."

    parts = []
    for a in articles:
        parts.append(
            f"Title: {a['title']}\n"
            f"Authors: {a.get('authors', '')}\n"
            f"Journal: {a['journal']}, {a['pub_date']}\n"
            f"URL: {a['url']}\n"
            f"Abstract: {a.get('abstract', 'No abstract available.')}\n"
        )
    return "\n---\n".join(parts)


def _format_preprint_articles(articles: list[dict]) -> str:
    if not articles:
        return "None today."

    parts = []
    for a in articles:
        parts.append(
            f"Title: {a['title']}\n"
            f"Authors: {a.get('authors', '')}\n"
            f"Server: {a['journal']}, {a['pub_date']}\n"
            f"DOI: {a.get('doi', '')}\n"
            f"URL: {a['url']}\n"
            f"Abstract: {a.get('abstract', 'No abstract available.')}\n"
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

    parts = ["## Valve Industry Stock Data"]
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

    private_list = ", ".join(config.PRIVATE_COMPANIES)
    parts.append(
        f"Note: {private_list} are private companies "
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


def _format_social_posts(posts: list[dict]) -> str:
    if not posts:
        return ""

    parts = ["## Social Media & Conference Highlights"]
    for p in posts:
        parts.append(
            f"Account: {p.get('source_name', '')}\n"
            f"Post: {p.get('snippet', p.get('title', ''))}\n"
            f"Date: {p['pub_date']}\n"
            f"URL: {p['url']}\n"
        )
        parts.append("---")
    return "\n".join(parts)


def _format_financial_news(articles: list[dict]) -> str:
    if not articles:
        return ""

    parts = ["## Financial News & SEC Filings"]
    for a in articles:
        parts.append(
            f"Title: {a['title']}\n"
            f"Source: {a.get('source_name', 'Unknown')}\n"
            f"Date: {a['pub_date']}\n"
            f"URL: {a['url']}\n"
            f"Details: {a.get('snippet', '')}\n"
        )
        parts.append("---")
    return "\n".join(parts)


def create_digest(
    pubmed_articles: list[dict],
    news_articles: list[dict],
    regulatory_articles: list[dict] = None,
    stock_data: dict = None,
    trials: list[dict] = None,
    preprint_articles: list[dict] = None,
    journal_articles: list[dict] = None,
    social_posts: list[dict] = None,
    financial_news: list[dict] = None,
) -> str:
    regulatory_articles = regulatory_articles or []
    stock_data = stock_data or {}
    trials = trials or []
    preprint_articles = preprint_articles or []
    journal_articles = journal_articles or []
    social_posts = social_posts or []
    financial_news = financial_news or []

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Build conditional instruction sections
    stock_instructions = ""
    stock_data_section = ""
    if stock_data:
        stock_instructions = (
            "- Include a <h2>Valve Industry Stocks</h2> section. "
            "For each ticker, use a bold company name as a subheading, then a bullet list "
            "with closing price, daily change ($ and %), 5-day range, and analyst target. "
            "Do NOT use HTML tables — use <strong> and <ul>/<li> only. "
            "Add a brief 1-2 sentence commentary on any significant moves. "
            f"Note that {', '.join(config.PRIVATE_COMPANIES)} are private companies."
        )
        stock_data_section = _format_stock_data(stock_data)

    trials_instructions = ""
    trials_data_section = ""
    if trials:
        trials_instructions = (
            "- Include a <h2>Clinical Trial Updates</h2> section. "
            "List each trial with its linked NCT ID, title, status, phase, enrollment, "
            "and sponsor using bullet lists. Group by valve type if helpful. "
            "Highlight any trials that changed status. "
            "Do NOT use HTML tables — use <ul>/<li> and <strong> only."
        )
        trials_data_section = _format_trials(trials)

    prompt = DIGEST_PROMPT_TEMPLATE.format(
        pubmed_count=len(pubmed_articles),
        pubmed_section=_format_pubmed_articles(pubmed_articles),
        journal_count=len(journal_articles),
        journal_section=_format_journal_articles(journal_articles),
        preprint_count=len(preprint_articles),
        preprint_section=_format_preprint_articles(preprint_articles),
        news_count=len(news_articles),
        news_section=_format_news_articles(news_articles),
        regulatory_count=len(regulatory_articles),
        regulatory_section=_format_regulatory(regulatory_articles),
        stock_instructions=stock_instructions,
        stock_data_section=stock_data_section,
        trials_instructions=trials_instructions,
        trials_data_section=trials_data_section,
        social_section=_format_social_posts(social_posts),
        financial_section=_format_financial_news(financial_news),
    )

    total = (
        len(pubmed_articles) + len(news_articles) + len(regulatory_articles)
        + len(preprint_articles) + len(journal_articles)
    )
    logger.info(
        f"Sending {total} articles + {len(stock_data)} stocks + {len(trials)} trials "
        f"+ {len(social_posts)} social + {len(financial_news)} financial "
        f"to Claude ({config.CLAUDE_MODEL}) for summarization"
    )

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=16384,
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
    preprint_articles: list[dict] = None,
    journal_articles: list[dict] = None,
    social_posts: list[dict] = None,
    financial_news: list[dict] = None,
) -> str:
    regulatory_articles = regulatory_articles or []
    stock_data = stock_data or {}
    trials = trials or []
    preprint_articles = preprint_articles or []
    journal_articles = journal_articles or []
    social_posts = social_posts or []
    financial_news = financial_news or []

    parts = ["<h2>The Valve Wire (AI summary unavailable)</h2>"]

    if pubmed_articles:
        parts.append("<h3>PubMed Articles</h3><ul>")
        for a in pubmed_articles:
            parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a> &mdash; '
                f'{a["journal"]}, {a["pub_date"]}</li>'
            )
        parts.append("</ul>")

    if journal_articles:
        parts.append("<h3>Journal Articles</h3><ul>")
        for a in journal_articles:
            parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a> &mdash; '
                f'{a.get("journal", "")}, {a["pub_date"]}</li>'
            )
        parts.append("</ul>")

    if preprint_articles:
        parts.append("<h3>Preprints</h3><ul>")
        for a in preprint_articles:
            parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a> &mdash; '
                f'{a.get("journal", "")}, {a["pub_date"]}</li>'
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
        parts.append("<h3>Valve Industry Stocks</h3><ul>")
        for ticker, d in stock_data.items():
            parts.append(
                f'<li><strong>{ticker} ({d["company"]})</strong>: '
                f'${d["close_price"]} ({d["change_pct"]:+.2f}%)</li>'
            )
        parts.append("</ul>")
        private_list = ", ".join(config.PRIVATE_COMPANIES)
        parts.append(f"<p><em>{private_list} are private (no stock data).</em></p>")

    if trials:
        parts.append("<h3>Clinical Trial Updates</h3><ul>")
        for t in trials:
            parts.append(
                f'<li><a href="{t["url"]}">{t["nct_id"]}</a>: {t["title"]} '
                f'&mdash; {t["status"]}, {t["sponsor"]}</li>'
            )
        parts.append("</ul>")

    if financial_news:
        parts.append("<h3>Financial News</h3><ul>")
        for a in financial_news:
            parts.append(
                f'<li><a href="{a["url"]}">{a["title"]}</a> &mdash; '
                f'{a.get("source_name", "")}</li>'
            )
        parts.append("</ul>")

    return "\n".join(parts)
