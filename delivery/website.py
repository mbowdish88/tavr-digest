"""Push structured JSON data to the website repo for Vercel deployment."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path

import config

logger = logging.getLogger(__name__)

WEBSITE_REPO = "mbowdish88/thevalvewire-site"


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
            return text[:1000]  # Cap at 1000 chars
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
            "image_url": a.get("og_image", None),
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

    # Format stock data
    stocks = {}
    for ticker, data in stock_data.items():
        if ticker.startswith("_"):
            continue
        if not isinstance(data, dict):
            continue
        stocks[ticker] = {
            "company": data.get("company", ticker),
            "price": data.get("close_price", 0),
            "change": data.get("change", 0),
            "change_pct": data.get("change_pct", 0),
            "change_6m": data.get("change_6m", 0),
            "change_6m_pct": data.get("change_6m_pct", 0),
        }

    # Get podcast info
    podcast_info = _get_latest_podcast()

    return {
        "date": today,
        "executive_summary": executive_summary,
        "key_points": key_points or [],
        "sections": sections,
        "stocks": stocks,
        "podcast": {"latest_episode": podcast_info},
        "digest_html": digest_html,
    }


def _get_latest_podcast() -> dict:
    """Get info about the latest podcast episode."""
    episodes_file = config.BASE_DIR / "data" / "podcast_episodes.json"
    if episodes_file.exists():
        try:
            episodes = json.loads(episodes_file.read_text())
            if episodes:
                ep = episodes[-1]
                return {
                    "title": ep.get("title", "The Valve Wire Weekly"),
                    "date": ep.get("date", ""),
                    "duration": ep.get("duration", ""),
                    "mp3_url": ep.get("mp3_url", ""),
                    "show_notes": ep.get("show_notes", ""),
                }
        except Exception:
            pass

    return {
        "title": "The Valve Wire Weekly",
        "date": "",
        "duration": "",
        "mp3_url": "",
        "show_notes": "No episodes yet.",
    }


def _github_api_put_file(token: str, path: str, content: str, message: str) -> bool:
    """Create or update a file in the website repo via GitHub API."""
    import base64
    import requests

    url = f"https://api.github.com/repos/{WEBSITE_REPO}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    # Check if file exists (need SHA for update)
    sha = None
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        sha = resp.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "committer": {"name": "valve-wire-bot", "email": "bot@thevalvewire.com"},
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        return True
    logger.error(f"GitHub API put failed for {path}: {resp.status_code} {resp.text[:200]}")
    return False


def _merge_with_previous(data: dict, token: str) -> dict:
    """If today's data is sparse, merge with previous day's data."""
    import requests
    import base64

    total_articles = sum(len(s["articles"]) for s in data["sections"].values())
    if total_articles >= 5:
        return data  # Enough content for today

    # Fetch previous latest.json from website repo
    url = f"https://api.github.com/repos/{WEBSITE_REPO}/contents/public/data/latest.json"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return data
        prev = json.loads(base64.b64decode(resp.json()["content"]))

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
    """Push the structured JSON to the website repo via GitHub API."""
    token = os.getenv("WEBSITE_GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
    if not token:
        logger.warning("No GITHUB_TOKEN, skipping website push")
        return False

    today = data["date"]

    # Merge with previous day if sparse
    data = _merge_with_previous(data, token)

    # Don't include digest_html in the website JSON (too large)
    website_data = {k: v for k, v in data.items() if k != "digest_html"}
    json_content = json.dumps(website_data, indent=2, default=str)

    # Push latest.json
    ok1 = _github_api_put_file(
        token, "public/data/latest.json", json_content,
        f"Update daily digest {today}",
    )

    # Push dated archive copy
    ok2 = _github_api_put_file(
        token, f"public/data/digests/{today}.json", json_content,
        f"Archive digest {today}",
    )

    if ok1 and ok2:
        logger.info(f"Website data pushed: latest.json + digests/{today}.json")
    return ok1 and ok2
