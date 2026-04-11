"""Publish podcast episode — upload to GitHub Releases and update RSS feed."""

from __future__ import annotations

import json
import logging
import subprocess
import uuid
from datetime import date, datetime
from email.utils import formatdate
from pathlib import Path
from time import mktime

from jinja2 import Environment, FileSystemLoader

import config

logger = logging.getLogger(__name__)


def _site_episodes_path() -> Path:
    return config.BASE_DIR / "site" / "public" / "data" / "podcast_episodes.json"


def _site_latest_json_path() -> Path:
    return config.BASE_DIR / "site" / "public" / "data" / "latest.json"


def _update_latest_json_podcast_block(episodes: list[dict]):
    """Propagate the episode list into latest.json so the website reflects
    new episodes immediately, without waiting for the next daily-digest run
    to regenerate latest.json. The daily pipeline short-circuits when no
    new articles are found, which leaves latest.json stale on quiet days.

    Format must match delivery.website._get_all_podcast_episodes output.
    """
    latest_path = _site_latest_json_path()
    if not latest_path.exists():
        return
    try:
        data = json.loads(latest_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Could not read {latest_path} to update podcast block: {e}")
        return
    formatted = [
        {
            "title": ep.get("title", "The Valve Wire Weekly"),
            "date": ep.get("episode_date", ep.get("date", "")),
            "duration": ep.get("duration", ""),
            "mp3_url": ep.get("mp3_url", ""),
            "show_notes": ep.get("description", ep.get("show_notes", "")),
            "show_notes_html": ep.get("show_notes_html", ""),
        }
        for ep in episodes
    ]
    data.setdefault("podcast", {})
    data["podcast"]["latest_episode"] = formatted[0] if formatted else {}
    data["podcast"]["all_episodes"] = formatted
    latest_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    logger.info(f"latest.json podcast block updated ({len(formatted)} episodes)")


def _load_episodes() -> list[dict]:
    """Load episode history from JSON file.

    Prefers data/podcast_episodes.json but falls back to site/public/data/
    so that CI runs (where data/ may not be committed) still see history.
    """
    for path in (config.PODCAST_EPISODES_DB, _site_episodes_path()):
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except Exception as e:
                logger.warning(f"Failed to read episodes from {path}: {e}")
    return []


def _save_episodes(episodes: list[dict]):
    """Save episode history to both data/ and site/public/data/, and
    propagate the new list into latest.json so the website updates without
    waiting for the next daily-digest run."""
    payload = json.dumps(episodes, indent=2, default=str)
    config.PODCAST_EPISODES_DB.parent.mkdir(parents=True, exist_ok=True)
    config.PODCAST_EPISODES_DB.write_text(payload, encoding="utf-8")
    site_path = _site_episodes_path()
    site_path.parent.mkdir(parents=True, exist_ok=True)
    site_path.write_text(payload, encoding="utf-8")
    _update_latest_json_podcast_block(episodes)


def _get_duration_str(mp3_path: Path) -> str:
    """Get duration string in HH:MM:SS format. Raises on failure — we
    refuse to ship an episode with a fake "00:00" duration."""
    from mutagen.mp3 import MP3
    audio = MP3(str(mp3_path))
    total_secs = int(audio.info.length)
    if total_secs <= 0:
        raise ValueError(
            f"mutagen returned non-positive duration ({total_secs}) for {mp3_path}"
        )
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    seconds = total_secs % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def upload_to_github_releases(mp3_path: Path, episode_date: str, title: str) -> str:
    """Upload MP3 to GitHub Releases and return the download URL.

    Args:
        mp3_path: Path to the MP3 file.
        episode_date: Date string for the release tag.
        title: Episode title.

    Returns:
        Download URL for the uploaded MP3.
    """
    tag = f"podcast-{episode_date}"
    filename = mp3_path.name

    logger.info(f"Creating GitHub release {tag}...")

    try:
        create_result = subprocess.run(
            [
                "gh", "release", "create", tag,
                str(mp3_path),
                "--title", title,
                "--notes", f"Auto-generated weekly podcast episode for {episode_date}",
                "--repo", config.GITHUB_REPO,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if create_result.returncode != 0:
            stderr_lower = (create_result.stderr or "").lower()
            if "already exists" in stderr_lower:
                logger.warning(f"Release {tag} already exists; uploading asset with --clobber")
                upload_result = subprocess.run(
                    [
                        "gh", "release", "upload", tag, str(mp3_path),
                        "--clobber",
                        "--repo", config.GITHUB_REPO,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if upload_result.returncode != 0:
                    logger.error(f"Asset re-upload to existing release failed: {upload_result.stderr}")
                    return ""
            else:
                logger.error(f"GitHub release failed: {create_result.stderr}")
                return ""

        download_url = (
            f"https://github.com/{config.GITHUB_REPO}/releases/download/{tag}/{filename}"
        )
        logger.info(f"Uploaded to GitHub Releases: {download_url}")
        return download_url

    except Exception as e:
        logger.error(f"GitHub release upload failed: {e}")
        return ""


def generate_rss_feed(episodes: list[dict]):
    """Generate the podcast RSS XML feed."""
    env = Environment(
        loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
        autoescape=False,
    )
    template = env.get_template("podcast_rss.xml")

    rss_xml = template.render(
        episodes=episodes,
        build_date=formatdate(localtime=True),
    )

    # Save to docs/podcast/ for GitHub Pages
    rss_dir = config.BASE_DIR / "docs" / "podcast"
    rss_dir.mkdir(parents=True, exist_ok=True)
    rss_path = rss_dir / "feed.xml"
    rss_path.write_text(rss_xml, encoding="utf-8")

    logger.info(f"RSS feed updated: {rss_path} ({len(episodes)} episodes)")

    # Also generate the landing page
    try:
        landing_template = env.get_template("podcast_landing.html")
        landing_html = landing_template.render(episodes=episodes)
        landing_path = rss_dir / "index.html"
        landing_path.write_text(landing_html, encoding="utf-8")
        logger.info(f"Landing page updated: {landing_path}")
    except Exception as e:
        logger.warning(f"Landing page generation failed: {e}")

    return rss_path


def publish_podcast(
    mp3_path: Path,
    episode_date: str,
    weekly_html: str = "",
    show_notes_html: str = "",
) -> dict:
    """Full publish pipeline: upload, update episode list, regenerate RSS.

    Args:
        mp3_path: Path to the final podcast MP3.
        episode_date: Date string (e.g., "2026-03-14").
        weekly_html: Weekly digest HTML for episode description.

    Returns:
        Episode metadata dict.
    """
    title = f"The Valve Wire Weekly - {episode_date}"
    duration = _get_duration_str(mp3_path)
    file_size = mp3_path.stat().st_size

    # Upload to GitHub Releases
    mp3_url = upload_to_github_releases(mp3_path, episode_date, title)
    if not mp3_url:
        logger.error("Failed to upload podcast. Skipping publish.")
        return {}

    # Build episode metadata
    episodes = _load_episodes()

    # Check if this episode already exists (re-run scenario)
    existing_index = next(
        (i for i, e in enumerate(episodes) if e.get("episode_date") == episode_date),
        None,
    )

    if existing_index is not None:
        existing = episodes[existing_index]
        episode_number = existing.get("number", existing_index + 1)
        guid = existing.get("guid") or str(uuid.uuid4())
    else:
        existing_numbers = [e.get("number", 0) for e in episodes if isinstance(e.get("number"), int)]
        episode_number = (max(existing_numbers) if existing_numbers else 0) + 1
        guid = str(uuid.uuid4())

    episode = {
        "number": episode_number,
        "title": title,
        "description": f"Weekly podcast covering transcatheter valve technology developments "
                       f"for the week ending {episode_date}.",
        "mp3_url": mp3_url,
        "file_size": file_size,
        "duration": duration,
        "pub_date_rfc2822": formatdate(localtime=True),
        "guid": guid,
        "episode_date": episode_date,
        "show_notes_html": show_notes_html,
    }

    if existing_index is not None:
        episodes[existing_index] = episode
    else:
        episodes.insert(0, episode)  # Newest first

    _save_episodes(episodes)

    # Regenerate RSS feed
    generate_rss_feed(episodes)

    logger.info(f"Published episode #{episode_number}: {title} ({duration})")
    return episode
