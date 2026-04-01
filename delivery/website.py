"""Write structured JSON data to site/public/data/ for Vercel deployment."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

import requests

import config

logger = logging.getLogger(__name__)

# Cache of fetched OG images to avoid re-fetching
_og_image_cache: dict[str, str | None] = {}


def _fetch_og_image(url: str) -> str | None:
    """Fetch the Open Graph image URL from an article page."""
    if not url or url in _og_image_cache:
        return _og_image_cache.get(url)

    try:
        resp = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (compatible; TheValveWire/1.0)"
        })
        if resp.status_code != 200:
            _og_image_cache[url] = None
            return None

        # Quick regex to find og:image — avoids needing BeautifulSoup
        import re
        match = re.search(
            r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
            resp.text[:10000],
            re.IGNORECASE,
        )
        if not match:
            match = re.search(
                r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
                resp.text[:10000],
                re.IGNORECASE,
            )

        image_url = match.group(1) if match else None
        _og_image_cache[url] = image_url
        if image_url:
            logger.debug(f"OG image found for {url[:60]}")
        return image_url
    except Exception:
        _og_image_cache[url] = None
        return None


def _classify_article(article: dict) -> str:
    """Classify an article into a website section based on its content."""
    title = (article.get("title", "") + " " + article.get("abstract", "")).lower()
    source = article.get("source", "").lower()

    # Check for surgical vs transcatheter comparisons first
    surgical_terms = ["surgical", "savr", "surgery vs", "vs tavr", "vs tavi", "compared to surgery",
                      "surgical replacement", "open heart", "sternotomy", "minimally invasive surgery"]
    if any(t in title for t in surgical_terms):
        return "surgical"

    # Aortic
    aortic_terms = ["tavr", "tavi", "aortic stenosis", "aortic valve", "sapien", "evolut",
                    "corevalve", "balloon-expandable", "self-expanding", "aortic regurgitation"]
    if any(t in title for t in aortic_terms):
        return "aortic"

    # Mitral
    mitral_terms = ["mitral", "mitraclip", "pascal", "tmvr", "tendyne", "intrepid",
                    "mitral regurgitation", "mitral repair", "mitral replacement", "teer",
                    "coapt", "mitra-fr"]
    if any(t in title for t in mitral_terms):
        return "mitral"

    # Tricuspid
    tricuspid_terms = ["tricuspid", "triclip", "ttvr", "evoque", "triluminate",
                       "tricuspid regurgitation", "tricuspid repair"]
    if any(t in title for t in tricuspid_terms):
        return "tricuspid"

    # Regulatory
    if article.get("source") == "regulatory" or "fda" in title or "approval" in title or "clearance" in title:
        return "regulatory"

    # Financial
    if article.get("source") == "financial" or source in ("bloomberg", "reuters", "sec"):
        return "financial"

    # Trials
    if article.get("nct_id") or "trial" in title or "clinical trial" in title:
        return "trials"

    # Default to aortic (most common topic)
    return "aortic"


def _article_type(article: dict) -> str:
    """Determine the display type for an article."""
    source = article.get("source", "")
    if source == "regulatory":
        return "Regulatory"
    if source in ("financial", "sec"):
        return "Financial"
    if article.get("nct_id"):
        return "Trial Update"
    if source in ("news", "google_news"):
        return "News"
    return "Research"


def _extract_executive_summary(digest_html: str) -> str:
    """Extract the executive summary section from the digest HTML."""
    if not digest_html:
        return ""
    import re
    # Look for executive summary section
    patterns = [
        r'<h2[^>]*>.*?Executive Summary.*?</h2>\s*(.*?)(?=<h2|$)',
        r'<h2[^>]*>.*?Key Takeaways.*?</h2>\s*(.*?)(?=<h2|$)',
        r'<h2[^>]*>.*?Overview.*?</h2>\s*(.*?)(?=<h2|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, digest_html, re.DOTALL | re.IGNORECASE)
        if match:
            # Strip HTML tags for clean text
            text = re.sub(r'<[^>]+>', ' ', match.group(1))
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:3000]  # Allow full executive summary
    return ""


def _extract_key_points(digest_html: str) -> list:
    """Extract key points from the digest HTML."""
    if not digest_html:
        return []
    import re
    points = []
    # Look for list items in the executive summary or key points section
    summary_match = re.search(
        r'<h2[^>]*>.*?(?:Executive Summary|Key Takeaways|Overview).*?</h2>(.*?)(?=<h2|$)',
        digest_html, re.DOTALL | re.IGNORECASE,
    )
    if summary_match:
        section = summary_match.group(1)
        # Extract list items
        items = re.findall(r'<li>(.*?)</li>', section, re.DOTALL)
        for item in items[:5]:
            text = re.sub(r'<[^>]+>', '', item).strip()
            if text:
                points.append(text)

    # If no list items, extract first few sentences from paragraphs
    if not points:
        p_match = re.findall(r'<p>(.*?)</p>', digest_html[:3000], re.DOTALL)
        for p in p_match[:3]:
            text = re.sub(r'<[^>]+>', '', p).strip()
            if len(text) > 40:
                points.append(text[:200])

    return points[:5]


def build_website_data(
    pubmed: list, news: list, regulatory: list,
    stock_data: dict, trials: list,
    preprints: list, journals: list,
    social: list, financial: list,
    digest_html: str = None,
    key_points: list = None,
) -> dict:
    """Build the structured JSON data for the website."""
    today = date.today().isoformat()

    # Extract executive summary and key points from digest HTML
    executive_summary = _extract_executive_summary(digest_html) if digest_html else ""
    if not key_points:
        key_points = _extract_key_points(digest_html) if digest_html else []

    # Section definitions
    sections = {
        "aortic": {"label": "Aortic Valve (TAVR/TAVI)", "color": "#C4787A", "articles": []},
        "mitral": {"label": "Mitral Valve (Repair & Replacement)", "color": "#8B5E6B", "articles": []},
        "tricuspid": {"label": "Tricuspid Valve (Repair & Replacement)", "color": "#4A7B8B", "articles": []},
        "surgical": {"label": "Surgical vs Transcatheter", "color": "#5B6B7B", "articles": []},
        "trials": {"label": "Clinical Trials Update", "color": "#7B5B8B", "articles": []},
        "regulatory": {"label": "Regulatory & Policy", "color": "#3B7B5B", "articles": []},
        "financial": {"label": "Financial Analysis", "color": "#8B7B3B", "articles": []},
    }

    # Fetch OG images for articles (limit to first 20 to avoid slowdowns)
    logger.info("Fetching article images...")
    all_source_articles = pubmed + preprints + journals + news + financial
    for a in all_source_articles[:20]:
        url = a.get("url", "")
        if url and not a.get("og_image"):
            a["og_image"] = _fetch_og_image(url)

    # Combine all articles
    all_articles = []
    for i, a in enumerate(pubmed + preprints + journals):
        all_articles.append({
            "id": f"r{i}",
            "type": _article_type(a),
            "title": a.get("title", "Untitled"),
            "source": a.get("journal") or a.get("source_name") or a.get("source", "Unknown"),
            "source_url": a.get("url", ""),
            "url": a.get("url", ""),
            "date": a.get("pub_date", today),
            "abstract": a.get("abstract", ""),
            "authors": a.get("authors", None),
            "image_url": a.get("og_image", None),
        })

    for i, a in enumerate(news):
        all_articles.append({
            "id": f"n{i}",
            "type": "News",
            "title": a.get("title", "Untitled"),
            "source": a.get("source_name", "News"),
            "source_url": a.get("url", ""),
            "url": a.get("url", ""),
            "date": a.get("pub_date", today),
            "abstract": a.get("snippet", a.get("abstract", "")),
            "authors": None,
            "image_url": a.get("og_image"),
        })

    for i, a in enumerate(regulatory):
        all_articles.append({
            "id": f"reg{i}",
            "type": "Regulatory",
            "title": a.get("title", "Untitled"),
            "source": a.get("source_name", "FDA"),
            "source_url": a.get("url", ""),
            "url": a.get("url", ""),
            "date": a.get("pub_date", today),
            "abstract": a.get("snippet", a.get("abstract", "")),
            "authors": None,
            "image_url": None,
        })

    for i, a in enumerate(financial):
        all_articles.append({
            "id": f"f{i}",
            "type": "Financial",
            "title": a.get("title", "Untitled"),
            "source": a.get("source_name", "Financial"),
            "source_url": a.get("url", ""),
            "url": a.get("url", ""),
            "date": a.get("pub_date", today),
            "abstract": a.get("snippet", a.get("abstract", "")),
            "authors": None,
            "image_url": None,
        })

    # Classify articles into sections
    for article in all_articles:
        section = _classify_article(article)
        sections[section]["articles"].append(article)

    # Add trial updates
    for i, t in enumerate(trials):
        sections["trials"]["articles"].append({
            "id": f"t{i}",
            "type": "Trial Update",
            "title": t.get("title", t.get("brief_title", "Untitled")),
            "source": "ClinicalTrials.gov",
            "source_url": f"https://clinicaltrials.gov/study/{t.get('nct_id', '')}",
            "url": f"https://clinicaltrials.gov/study/{t.get('nct_id', '')}",
            "date": t.get("last_update", today),
            "abstract": t.get("brief_summary", ""),
            "authors": None,
            "image_url": None,
            "nct_id": t.get("nct_id"),
            "phase": t.get("phase"),
            "status": t.get("overall_status", t.get("status")),
            "sponsor": t.get("lead_sponsor", t.get("sponsor")),
        })

    # Format stock data with price history
    stocks = {}
    for ticker, data in stock_data.items():
        if ticker.startswith("_"):
            continue
        if not isinstance(data, dict):
            continue

        # Get price history for charts
        history = []
        if data.get("chart_url"):
            # The history is stored during fetch_stock_data in all_histories
            # We need to pass it through — check for dates/closes arrays
            pass

        history = data.get("price_history", {})
        stocks[ticker] = {
            "company": data.get("company", ticker),
            "price": data.get("close_price", 0),
            "change": data.get("change", 0),
            "change_pct": data.get("change_pct", 0),
            "change_6m": data.get("change_6m", 0),
            "change_6m_pct": data.get("change_6m_pct", 0),
            "high_6m": data.get("high_6m", 0),
            "low_6m": data.get("low_6m", 0),
            "market_cap": data.get("market_cap"),
            "pe_ratio": data.get("pe_ratio"),
            "target_price": data.get("target_price"),
            "recommendation": data.get("recommendation", ""),
            "next_earnings_date": data.get("next_earnings_date"),
            "price_history": history,
        }

    # Get podcast episodes
    all_episodes = _get_all_podcast_episodes()
    latest_episode = all_episodes[0] if all_episodes else {
        "title": "The Valve Wire Weekly", "date": "", "duration": "",
        "mp3_url": "", "show_notes": "No episodes yet.",
    }

    return {
        "date": today,
        "executive_summary": executive_summary,
        "key_points": key_points or [],
        "sections": sections,
        "stocks": stocks,
        "podcast": {
            "latest_episode": latest_episode,
            "all_episodes": all_episodes,
        },
        "digest_html": digest_html,
    }


def _get_all_podcast_episodes() -> list:
    """Get all podcast episodes."""
    episodes_file = config.BASE_DIR / "data" / "podcast_episodes.json"
    if episodes_file.exists():
        try:
            episodes = json.loads(episodes_file.read_text())
            return [
                {
                    "title": ep.get("title", "The Valve Wire Weekly"),
                    "date": ep.get("episode_date", ep.get("date", "")),
                    "duration": ep.get("duration", ""),
                    "mp3_url": ep.get("mp3_url", ""),
                    "show_notes": ep.get("description", ep.get("show_notes", "")),
                    "show_notes_html": ep.get("show_notes_html", ""),
                }
                for ep in reversed(episodes)  # newest first
            ]
        except Exception:
            pass
    return []



def _get_site_data_dir() -> Path:
    """Return the path to the website data directory within this repo."""
    return config.BASE_DIR / "site" / "public" / "data"


def _merge_with_previous(data: dict) -> dict:
    """If today's data is sparse, merge with previous day's data from local site/."""
    total_articles = sum(len(s["articles"]) for s in data["sections"].values())
    if total_articles >= 5:
        return data  # Enough content for today

    latest_path = _get_site_data_dir() / "latest.json"
    try:
        if not latest_path.exists():
            return data
        prev = json.loads(latest_path.read_text(encoding="utf-8"))

        # Merge: keep today's articles, fill empty sections with previous day's
        for section_key, section in data["sections"].items():
            if not section["articles"] and section_key in prev.get("sections", {}):
                prev_articles = prev["sections"][section_key].get("articles", [])
                if prev_articles:
                    # Mark them as from a previous day
                    for a in prev_articles:
                        a["type"] = f"Recent {a.get('type', 'Article')}"
                    section["articles"] = prev_articles

        # Use previous executive summary if we don't have one
        if not data.get("executive_summary") and prev.get("executive_summary"):
            data["executive_summary"] = prev["executive_summary"]

        # Use previous key points if we don't have any
        if not data.get("key_points") and prev.get("key_points"):
            data["key_points"] = prev["key_points"]

        logger.info(f"Merged with previous day's data (today had {total_articles} articles)")
    except Exception as e:
        logger.warning(f"Could not merge with previous data: {e}")

    return data


def push_to_website(data: dict) -> bool:
    """Write structured JSON to site/public/data/ for Vercel deployment.

    The site now lives inside this repo as site/. Writing locally means the
    pipeline's git commit + push carries the website data to Vercel automatically.
    No GitHub API token needed.
    """
    today = data["date"]
    data_dir = _get_site_data_dir()
    digests_dir = data_dir / "digests"

    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    digests_dir.mkdir(parents=True, exist_ok=True)

    # Merge with previous day if sparse
    data = _merge_with_previous(data)

    # Don't include digest_html in the website JSON (too large)
    website_data = {k: v for k, v in data.items() if k != "digest_html"}
    json_content = json.dumps(website_data, indent=2, default=str)

    try:
        # Write latest.json
        latest_path = data_dir / "latest.json"
        latest_path.write_text(json_content, encoding="utf-8")
        logger.info(f"Wrote {latest_path} ({len(json_content)} bytes)")

        # Write dated archive copy
        archive_path = digests_dir / f"{today}.json"
        archive_path.write_text(json_content, encoding="utf-8")
        logger.info(f"Wrote {archive_path}")

        return True
    except Exception as e:
        logger.error(f"Failed to write website data: {e}")
        return False
