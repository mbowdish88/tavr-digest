"""Generate show notes with timestamps, article links, and episode summary."""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path

import config

logger = logging.getLogger(__name__)

SECTION_NAMES = {
    "intro": "Introduction",
    "top_stories": "Top Stories",
    "aortic": "Aortic Valve (TAVR/TAVI)",
    "mitral": "Mitral Valve (Repair & Replacement)",
    "tricuspid": "Tricuspid Valve (Repair & Replacement)",
    "trials": "Clinical Trials Update",
    "surgical_comparison": "Surgical vs. Transcatheter",
    "market": "Market & Industry",
    "weekend": "Weekend News",
    "closing": "Closing Thoughts",
}


def _format_timestamp(ms: int) -> str:
    """Convert milliseconds to MM:SS format."""
    total_secs = ms // 1000
    minutes = total_secs // 60
    seconds = total_secs % 60
    return f"{minutes:02d}:{seconds:02d}"


def _extract_links(html_content: str) -> list[dict]:
    """Extract all hyperlinks from HTML content."""
    links = []
    pattern = r'<a\s+href="([^"]+)"[^>]*>([^<]+)</a>'
    for match in re.finditer(pattern, html_content, re.IGNORECASE):
        url = match.group(1)
        text = html.unescape(match.group(2)).strip()
        if url and text and not url.startswith("mailto:"):
            links.append({"url": url, "text": text})
    return links


def generate_show_notes(
    script: list[dict],
    timestamps: list[dict],
    episode_date: str,
    weekly_html: str = "",
    duration_str: str = "",
) -> tuple[str, str]:
    """Generate show notes in markdown and HTML formats.

    Args:
        script: The podcast script segments.
        timestamps: List of section timestamp dicts from the assembler.
        episode_date: Date string (e.g., "2026-03-14").
        weekly_html: The weekly digest HTML for extracting article links.
        duration_str: Episode duration string.

    Returns:
        Tuple of (markdown, html) show notes.
    """
    lines = []
    lines.append(f"# The Valve Wire Weekly - {episode_date}")
    lines.append("")

    if duration_str:
        lines.append(f"**Duration:** {duration_str}")
        lines.append(f"**Hosts:** Nolan Beckett & Claire")
        lines.append("")

    # Timestamps
    lines.append("## Timestamps")
    lines.append("")
    for ts in timestamps:
        section_name = SECTION_NAMES.get(ts["section"], ts["section"].replace("_", " ").title())
        lines.append(f"- [{_format_timestamp(ts['offset_ms'])}] {section_name}")
    lines.append("")

    # Episode summary — use the intro section text
    intro_texts = [s["text"] for s in script if s.get("section") == "intro"]
    if intro_texts:
        lines.append("## Episode Summary")
        lines.append("")
        lines.append(" ".join(intro_texts[:3]))
        lines.append("")

    # Articles discussed
    if weekly_html:
        links = _extract_links(weekly_html)
        if links:
            # Deduplicate by URL
            seen = set()
            unique_links = []
            for link in links:
                if link["url"] not in seen:
                    seen.add(link["url"])
                    unique_links.append(link)

            lines.append("## Articles & Sources Discussed")
            lines.append("")
            for link in unique_links[:30]:  # Cap at 30
                lines.append(f"- [{link['text']}]({link['url']})")
            lines.append("")

    # Subscribe CTA
    lines.append("## Subscribe")
    lines.append("")
    lines.append("- Newsletter: [The Valve Wire on Beehiiv](https://thevalvewire.beehiiv.com)")
    lines.append("- Contact: [nolan.beckett@pm.me](mailto:nolan.beckett@pm.me)")
    lines.append("")

    markdown = "\n".join(lines)

    # Convert to simple HTML for RSS
    html_lines = []
    html_lines.append(f"<h3>The Valve Wire Weekly - {episode_date}</h3>")
    if duration_str:
        html_lines.append(f"<p><strong>Duration:</strong> {duration_str} | <strong>Hosts:</strong> Nolan Beckett &amp; Claire</p>")

    html_lines.append("<h4>Timestamps</h4><ul>")
    for ts in timestamps:
        section_name = SECTION_NAMES.get(ts["section"], ts["section"].replace("_", " ").title())
        html_lines.append(f"<li>[{_format_timestamp(ts['offset_ms'])}] {section_name}</li>")
    html_lines.append("</ul>")

    if intro_texts:
        html_lines.append(f"<h4>Summary</h4><p>{html.escape(' '.join(intro_texts[:3]))}</p>")

    if weekly_html:
        links = _extract_links(weekly_html)
        if links:
            seen = set()
            html_lines.append("<h4>Articles &amp; Sources</h4><ul>")
            for link in links:
                if link["url"] not in seen:
                    seen.add(link["url"])
                    html_lines.append(f'<li><a href="{html.escape(link["url"])}">{html.escape(link["text"])}</a></li>')
            html_lines.append("</ul>")

    html_lines.append('<p>Subscribe: <a href="https://thevalvewire.beehiiv.com">The Valve Wire Newsletter</a></p>')

    show_notes_html = "\n".join(html_lines)

    # Save markdown file
    md_path = config.PODCAST_DIR / f"{episode_date}_show_notes.md"
    md_path.write_text(markdown, encoding="utf-8")
    logger.info(f"Show notes saved: {md_path.name}")

    return markdown, show_notes_html
