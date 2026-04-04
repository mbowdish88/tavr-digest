from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta

from anthropic import Anthropic

import config

logger = logging.getLogger(__name__)

# Major meetings calendar — update annually
# Format: (name, approximate_start_month, approximate_start_day, duration_days)
MAJOR_MEETINGS = [
    ("STS Annual Meeting", 1, 25, 4),       # Late January
    ("ACC Scientific Sessions", 3, 27, 4),   # Late March (2026: Mar 27-30)
    ("AATS Annual Meeting", 5, 3, 4),        # Early May
    ("ESC Congress", 8, 29, 4),              # Late August
    ("TCT Conference", 10, 27, 4),           # Late October
    ("AHA Scientific Sessions", 11, 15, 4),  # Mid November
    ("EACTS Annual Meeting", 10, 7, 4),      # Early October
]


def _get_active_meeting_context(today: date) -> str:
    """Check if a major meeting is currently happening and return context."""
    for name, month, day, duration in MAJOR_MEETINGS:
        try:
            start = date(today.year, month, day)
            end = start + timedelta(days=duration)
            # Include 1 day before and 2 days after for pre/post coverage
            if (start - timedelta(days=1)) <= today <= (end + timedelta(days=2)):
                return (
                    f"## ACTIVE MEETING: {name}\n"
                    f"The {name} is currently taking place ({start.strftime('%B %d')} - "
                    f"{end.strftime('%B %d, %Y')}). Pay special attention to:\n"
                    f"- Late-breaking clinical trial presentations\n"
                    f"- Simultaneous publications in NEJM, JACC, Lancet, EHJ\n"
                    f"- Press releases from Edwards, Medtronic, Abbott, Boston Scientific\n"
                    f"- TCTMD and Cardiovascular Business meeting coverage\n"
                    f"- Guideline updates or consensus statements\n"
                    f"When reporting on articles, note if they were presented at {name}. "
                    f"Frame the digest as covering this major meeting."
                )
        except ValueError:
            continue
    return ""

SYSTEM_PROMPT = """\
You are a medical literature and market analyst specializing in structural heart \
disease, including transcatheter aortic (TAVR/TAVI), mitral (MitraClip, PASCAL, TMVR), \
and tricuspid (TriClip, TTVR) valve therapies. You produce a daily newsletter called \
"The Valve Wire" by E. Nolan Beckett, for a broad audience: cardiac surgeons, \
interventional cardiologists, trainees, patients with valvular heart disease, industry \
stakeholders, and regulatory agencies. The digest is published on Beehiiv, so it should \
read like a polished, engaging newsletter — authoritative but approachable, with clear \
narrative flow. The visual design uses a navy/gold color scheme with Georgia serif \
typography — your HTML output should complement this aesthetic.

JOURNAL HIERARCHY FOR EMPHASIS: When writing the executive summary and key points, \
prioritize findings from top-tier journals in this order: \
1. NEJM  2. JAMA  3. JACC  4. Lancet  5. European Heart Journal  \
6. JACC: Cardiovascular Interventions  7. Annals of Thoracic Surgery, JTCVS, EJCTS. \
Articles from NEJM, JAMA, JACC, Lancet, or EHJ should ALWAYS be highlighted in the \
executive summary, even on busy days. Lower-tier findings can be summarized more briefly.

CRITICAL EDITORIAL STANCE: Many structural heart technologies have gotten ahead of \
the science and clinical guidelines. You must be BALANCED and CIRCUMSPECT:
- Always present competing arguments for and against favorable findings
- Flag study limitations: non-randomized designs, industry sponsorship, short follow-up, \
small samples, single-center data
- When reporting favorable transcatheter outcomes, note durability concerns, patient \
selection biases, complication rates, and surgical alternatives
- Never present transcatheter superiority as settled when long-term data or guidelines \
don't support it
- Reference critical perspectives where relevant (Bowdish, Badhwar, Mehaffey, Kaul, \
Miller, Chikwe have published on therapies outpacing evidence)
- Tone: expert skepticism — enthusiastic about real advances but always questioning. \
Think peer review, not press release."""

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
    parts.append(
        "NOTE: Chart images are available and will be embedded in the HTML output. "
        "Reference them using <img> tags where indicated below."
    )

    combined_chart = stock_data.get("_combined_chart_url", "")
    if combined_chart:
        parts.append(f"COMBINED 6-MONTH CHART URL: {combined_chart}")
        parts.append("(Embed this chart at the top of the Valve Industry Stocks section)")

    for ticker, data in stock_data.items():
        if ticker.startswith("_"):
            continue
        parts.append(
            f"Ticker: {ticker} ({data['company']})\n"
            f"Close: ${data['close_price']} (date: {data['close_date']})\n"
            f"Daily Change: {data['change']:+.2f} ({data['change_pct']:+.2f}%)\n"
            f"5-Day Range: ${data['low_5d']} - ${data['high_5d']}\n"
            f"6-Month Range: ${data['low_6m']} - ${data['high_6m']}\n"
            f"6-Month Change: {data['change_6m']:+.2f} ({data['change_6m_pct']:+.2f}%)\n"
            f"Volume: {data['volume']:,}"
        )

        # Market fundamentals
        fundamentals = []
        if data.get("market_cap"):
            cap_b = data["market_cap"] / 1e9
            fundamentals.append(f"Market Cap: ${cap_b:.1f}B")
        if data.get("pe_ratio"):
            fundamentals.append(f"P/E (trailing): {data['pe_ratio']}")
        if data.get("forward_pe"):
            fundamentals.append(f"P/E (forward): {data['forward_pe']}")
        if data.get("beta"):
            fundamentals.append(f"Beta: {data['beta']}")
        if data.get("fifty_two_high"):
            fundamentals.append(f"52-Week Range: ${data['fifty_two_low']} - ${data['fifty_two_high']}")
        if fundamentals:
            parts.append("Fundamentals: " + " | ".join(fundamentals))

        # Analyst targets
        if data.get("target_price"):
            parts.append(
                f"Analyst Target: ${data['target_price']} "
                f"(range: ${data['target_low']} - ${data['target_high']}, "
                f"{data['num_analysts']} analysts)\n"
                f"Recommendation: {data['recommendation']}"
            )

        # Earnings
        if data.get("next_earnings_date"):
            earnings_info = f"Next Earnings: {data['next_earnings_date']}"
            if data.get("earnings_estimate"):
                earnings_info += f" (EPS est: ${data['earnings_estimate']})"
            if data.get("revenue_estimate"):
                rev_b = data["revenue_estimate"] / 1e9
                earnings_info += f" (Rev est: ${rev_b:.2f}B)"
            parts.append(earnings_info)

        # Events / news
        if data.get("events"):
            parts.append("Recent Events:")
            for ev in data["events"]:
                parts.append(f"  - [{ev['date']}] {ev['title']} ({ev['source']})")

        # Individual chart
        if data.get("chart_url"):
            parts.append(f"INDIVIDUAL CHART URL: {data['chart_url']}")

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
        combined_chart = stock_data.get("_combined_chart_url", "")
        chart_instruction = ""
        if combined_chart:
            chart_instruction = (
                f'Start the section with the combined chart: <img src="{combined_chart}" '
                f'alt="6-Month Valve Industry Stock Performance" style="max-width:100%;height:auto;">\n'
                "Then for each company, embed its individual chart using the INDIVIDUAL CHART URL "
                'provided: <img src="URL" alt="TICKER 6-Month Chart" style="max-width:100%;height:auto;">\n'
            )
        stock_instructions = (
            "- Include a <h2>Valve Industry Stocks</h2> section with detailed analysis.\n"
            f"{chart_instruction}"
            "- For each ticker, use <h3>Company Name (TICKER)</h3> then provide:\n"
            "  - Current price, daily change, and 6-month performance\n"
            "  - Market cap, P/E ratios, beta, and 52-week range\n"
            "  - Analyst consensus target and recommendation\n"
            "  - Next earnings date with EPS/revenue estimates\n"
            "  - Commentary on recent events affecting the stock\n"
            "- After individual stocks, include a brief market outlook paragraph connecting "
            "company performance to broader structural heart industry trends.\n"
            f"- Note that {', '.join(config.PRIVATE_COMPANIES)} are private companies."
        )
        stock_data_section = _format_stock_data(stock_data)

    trials_instructions = ""
    trials_data_section = ""
    if trials:
        trials_instructions = (
            "- Include a <h2>Clinical Trial Updates</h2> section. "
            "List each trial with its linked NCT ID, title, status, phase, enrollment, "
            "and sponsor using bullet lists. Group by valve type (Aortic, Mitral Repair, "
            "Mitral Replacement, Tricuspid Repair, Tricuspid Replacement). "
            "Trials marked [LANDMARK] are major pivotal trials — give these extra attention "
            "and context about their significance. Highlight any trials that changed status. "
            "Include specific trial names like REPAIR-MR, PRIMATY, TRILUMINATE, CLASP TR, "
            "APOLLO, TRISCEND, PARTNER, COAPT when referencing these landmark studies. "
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
        f"to Claude (claude-opus-4-6) for summarization"
    )

    # Check if a major meeting is occurring
    from datetime import date as _date
    _today = _date.today()
    _meeting_context = _get_active_meeting_context(_today)

    # Inject guidelines knowledge into the system prompt
    from knowledge import get_full_knowledge_context
    knowledge = get_full_knowledge_context()
    system_with_knowledge = SYSTEM_PROMPT
    if _meeting_context:
        system_with_knowledge += "\n\n" + _meeting_context
        logger.info(f"Active meeting context injected")
    if knowledge:
        system_with_knowledge += "\n\n" + knowledge
        logger.info(f"Injected {len(knowledge)} chars of guidelines context")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16384,
        system=system_with_knowledge,
        messages=[{"role": "user", "content": prompt}],
        timeout=21600.0,
    )

    digest_html = message.content[0].text
    logger.info(
        f"Digest generated: {len(digest_html)} chars, "
        f"tokens used: {message.usage.input_tokens} in / {message.usage.output_tokens} out"
    )

    return digest_html


def _extract_key_numbers(text: str) -> list[str]:
    """Extract percentages, p-values, sample sizes, and CIs from text."""
    if not text:
        return []
    numbers = []
    # Percentages: 42.3%, 15%
    numbers.extend(re.findall(r'\d+\.?\d*\s*%', text))
    # P-values: p<0.001, p=0.03, P = 0.05
    numbers.extend(re.findall(r'[Pp]\s*[<>=]\s*0?\.\d+', text))
    # Confidence intervals: 95% CI 1.2-3.4, CI: 0.8 to 1.5
    numbers.extend(re.findall(r'(?:95|99)\s*%?\s*CI\s*[:\s]*[\d.]+ *[-–to]+ *[\d.]+', text, re.IGNORECASE))
    # Hazard/odds ratios: HR 0.75, OR 2.1
    numbers.extend(re.findall(r'(?:HR|OR|RR)\s*[=:]?\s*\d+\.?\d*', text, re.IGNORECASE))
    # Sample sizes: n=500, N = 1,200, enrolled 500 patients
    numbers.extend(re.findall(r'[Nn]\s*=\s*[\d,]+', text))
    return numbers


def _extract_sample_size(text: str) -> int | None:
    """Try to extract sample size from abstract text."""
    if not text:
        return None
    # Common patterns: "N=500", "n = 1,200", "enrolled 500 patients",
    # "500 patients", "included 1200 subjects"
    patterns = [
        r'[Nn]\s*=\s*([\d,]+)',
        r'(?:enrolled|included|recruited|randomized)\s+([\d,]+)\s+(?:patients|subjects|participants)',
        r'([\d,]+)\s+(?:patients|subjects|participants)\s+(?:were|who)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            try:
                return int(m.group(1).replace(',', ''))
            except ValueError:
                continue
    return None


def _classify_study_design(text: str) -> str:
    """Classify study design from abstract text."""
    if not text:
        return ""
    text_lower = text.lower()
    if 'randomized' in text_lower or 'randomised' in text_lower:
        if 'controlled trial' in text_lower or 'clinical trial' in text_lower:
            return "Randomized controlled trial"
        return "Randomized trial"
    if 'meta-analysis' in text_lower or 'meta analysis' in text_lower:
        return "Meta-analysis"
    if 'systematic review' in text_lower:
        return "Systematic review"
    if 'retrospective' in text_lower:
        return "Retrospective study"
    if 'prospective' in text_lower:
        if 'registry' in text_lower:
            return "Prospective registry"
        return "Prospective study"
    if 'registry' in text_lower:
        return "Registry study"
    if 'cohort' in text_lower:
        return "Cohort study"
    if 'case report' in text_lower or 'case series' in text_lower:
        return "Case report/series"
    if 'observational' in text_lower:
        return "Observational study"
    return ""


def _classify_section(article: dict) -> str:
    """Classify an article into a valve section based on title/abstract."""
    text = (article.get('title', '') + ' ' + article.get('abstract', '')).lower()
    if any(kw in text for kw in ['tavr', 'tavi', 'aortic valve', 'savr', 'aortic stenosis']):
        return "aortic"
    if any(kw in text for kw in ['mitral', 'mitraclip', 'pascal', 'tmvr', 'mitral regurgitation']):
        return "mitral"
    if any(kw in text for kw in ['tricuspid', 'triclip', 'ttvr', 'tricuspid regurgitation']):
        return "tricuspid"
    return "general"


def _extract_first_key_finding(text: str) -> str:
    """Extract the most likely key finding sentence from an abstract."""
    if not text:
        return ""
    # Look for sentences containing results-like keywords
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result_keywords = [
        'significant', 'reduction', 'improvement', 'mortality', 'outcome',
        'survival', 'compared', 'superior', 'non-inferior', 'hazard ratio',
        'odds ratio', 'p <', 'p=', 'p =', 'difference', 'associated with',
    ]
    for sent in sentences:
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in result_keywords):
            return sent.strip()
    # Fallback: last sentence of abstract often contains conclusion
    if sentences:
        return sentences[-1].strip()
    return ""


def extract_structured_sidecar(
    pubmed_articles: list[dict],
    journal_articles: list[dict],
    preprint_articles: list[dict],
    news_articles: list[dict],
    regulatory_articles: list[dict],
) -> dict:
    """Build structured article metadata from raw inputs (no Claude call).

    Returns a dict matching the sidecar JSON schema with date and articles list.
    """
    today = date.today().isoformat()
    articles = []

    # Process PubMed articles
    for a in (pubmed_articles or []):
        abstract = a.get('abstract', '')
        articles.append({
            "title": a.get('title', ''),
            "journal": a.get('journal', ''),
            "url": a.get('url', ''),
            "pmid": a.get('id', ''),
            "authors": a.get('authors', ''),
            "study_design": _classify_study_design(abstract),
            "sample_size": _extract_sample_size(abstract),
            "key_finding": _extract_first_key_finding(abstract),
            "key_numbers": _extract_key_numbers(abstract),
            "section": _classify_section(a),
        })

    # Process journal articles
    for a in (journal_articles or []):
        abstract = a.get('abstract', '')
        articles.append({
            "title": a.get('title', ''),
            "journal": a.get('journal', ''),
            "url": a.get('url', ''),
            "pmid": "",
            "authors": a.get('authors', ''),
            "study_design": _classify_study_design(abstract),
            "sample_size": _extract_sample_size(abstract),
            "key_finding": _extract_first_key_finding(abstract),
            "key_numbers": _extract_key_numbers(abstract),
            "section": _classify_section(a),
        })

    # Process preprints
    for a in (preprint_articles or []):
        abstract = a.get('abstract', '')
        articles.append({
            "title": a.get('title', ''),
            "journal": a.get('journal', ''),
            "url": a.get('url', ''),
            "pmid": "",
            "authors": a.get('authors', ''),
            "study_design": _classify_study_design(abstract),
            "sample_size": _extract_sample_size(abstract),
            "key_finding": _extract_first_key_finding(abstract),
            "key_numbers": _extract_key_numbers(abstract),
            "section": _classify_section(a),
        })

    # News and regulatory get lighter extraction
    for a in (news_articles or []):
        snippet = a.get('snippet', '')
        articles.append({
            "title": a.get('title', ''),
            "journal": a.get('source_name', ''),
            "url": a.get('url', ''),
            "pmid": "",
            "authors": "",
            "study_design": "",
            "sample_size": None,
            "key_finding": snippet[:200] if snippet else "",
            "key_numbers": _extract_key_numbers(snippet),
            "section": _classify_section(a),
        })

    for a in (regulatory_articles or []):
        snippet = a.get('snippet', '')
        articles.append({
            "title": a.get('title', ''),
            "journal": a.get('source_name', 'FDA'),
            "url": a.get('url', ''),
            "pmid": "",
            "authors": "",
            "study_design": "",
            "sample_size": None,
            "key_finding": snippet[:200] if snippet else "",
            "key_numbers": _extract_key_numbers(snippet),
            "section": "regulatory",
        })

    return {"date": today, "articles": articles}


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
            if not isinstance(d, dict):  # skip _combined_chart_url and other metadata keys
                continue
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
