"""One-off re-render of the 2026-04-25 podcast episode.

Three phases. Run each separately so the operator can approve between them:

  python scripts/rerender_2026-04-25.py --phase script
  # review data/podcast/2026-04-25_script.json, then:
  python scripts/rerender_2026-04-25.py --phase synthesize
  # listen to data/podcast/2026-04-25_valve_wire_weekly.mp3, then:
  python scripts/rerender_2026-04-25.py --phase publish

Phase 1 generates the script via Claude (cost ~$0.40) and writes it
to data/podcast/2026-04-25_script.json. Stops there.

Phase 2 reads that script, runs OpenAI TTS for any segment whose audio
is not already cached, assembles with the clip-safe assembler, and runs
ffprobe to verify peak < 0 dBFS. Writes the MP3 to data/podcast/.
Stops there. Cost ~$0.50-1.00 depending on cache hits.

Phase 3 uploads the local MP3 to GitHub release podcast-2026-04-25 with
--clobber, updates podcast_episodes.json, regenerates RSS, propagates
to latest.json. Same release tag preserves the public MP3 URL so RSS
subscribers see no churn.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config
from podcast.scriptwriter import generate_podcast_script
from podcast.synthesizer import synthesize_segments
from podcast.assembler import assemble_podcast
from podcast.publisher import publish_podcast, _get_duration_str
from podcast.show_notes import generate_show_notes
from main import get_week_sidecars
from datetime import date, timedelta

EPISODE_DATE = "2026-04-25"
SCRIPT_PATH = config.BASE_DIR / "data" / "podcast" / f"{EPISODE_DATE}_script.json"
WEEKLY_HTML_PATH = config.BASE_DIR / "site" / "public" / "data" / f"weekly_{EPISODE_DATE}.html"
FEATURED_PATH = config.BASE_DIR / "tasks" / f"featured_{EPISODE_DATE}.md"
MP3_PATH = config.BASE_DIR / "data" / "podcast" / f"{EPISODE_DATE}_valve_wire_weekly.mp3"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("rerender")


def phase_script():
    if not WEEKLY_HTML_PATH.exists():
        sys.exit(f"Missing weekly HTML: {WEEKLY_HTML_PATH}")
    weekly_html = WEEKLY_HTML_PATH.read_text(encoding="utf-8")
    log.info(f"Loaded weekly HTML: {len(weekly_html)} chars")

    if FEATURED_PATH.exists():
        featured_text = FEATURED_PATH.read_text(encoding="utf-8")
        weekly_html = (
            f"<h2>FEATURED STORIES — Full Text (editor-curated)</h2>\n"
            f"<pre>{featured_text}</pre>\n"
            f"<hr>\n"
            + weekly_html
        )
        log.info(f"Prepended {FEATURED_PATH.name}: {len(featured_text)} chars")
    else:
        log.warning(f"No featured file at {FEATURED_PATH}")

    episode_dt = date.fromisoformat(EPISODE_DATE)
    start_str = (episode_dt - timedelta(days=6)).strftime("%B %d")
    end_str = episode_dt.strftime("%B %d, %Y")

    article_metadata = get_week_sidecars(episode_dt)
    log.info(f"Loaded {len(article_metadata) if article_metadata else 0} article metadata records")

    log.info("Calling Claude scriptwriter...")
    script = generate_podcast_script(
        weekly_html, start_str, end_str, episode_number=4,
        article_metadata=article_metadata or None,
    )
    if not script:
        sys.exit("Script generation returned empty")

    SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCRIPT_PATH.write_text(json.dumps(script, indent=2), encoding="utf-8")
    log.info(f"Wrote script: {SCRIPT_PATH} ({len(script)} segments)")

    # Print a quick view of the first ~10 segments so reviewer sees ordering
    print("\n--- FIRST 10 SEGMENTS (review for WSJ leading the Top Stories) ---")
    for i, seg in enumerate(script[:10]):
        section = seg.get("section", "?")
        speaker = seg.get("speaker", "?")
        text = seg.get("text", "")[:140]
        print(f"  [{i:2d}] {section:18s} {speaker}: {text}")
    print("\nReview full script at:", SCRIPT_PATH)
    print("Then run: python scripts/rerender_2026-04-25.py --phase synthesize")


def phase_synthesize():
    if not SCRIPT_PATH.exists():
        sys.exit(f"Missing script (run --phase script first): {SCRIPT_PATH}")
    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    log.info(f"Loaded script: {len(script)} segments")

    log.info("Calling OpenAI TTS for segments...")
    segments = synthesize_segments(script, EPISODE_DATE)
    successful = sum(1 for s in segments if s.get("audio_path"))
    log.info(f"TTS done: {successful}/{len(segments)} segments synthesized")
    if successful == 0:
        sys.exit("No segments synthesized — aborting")

    episode_dt = date.fromisoformat(EPISODE_DATE)
    start_str = (episode_dt - timedelta(days=6)).strftime("%B %d")
    end_str = episode_dt.strftime("%B %d, %Y")
    title = f"The Valve Wire Weekly - Week of {start_str} to {end_str}"

    log.info("Assembling with clip-safe assembler...")
    mp3_path, timestamps = assemble_podcast(segments, EPISODE_DATE, title)
    log.info(f"Assembled: {mp3_path}")

    # Verify no clipping
    log.info("Running ffprobe peak check...")
    result = subprocess.run(
        ["ffmpeg", "-i", str(mp3_path), "-af", "astats=measure_overall=Peak_level+Max_level",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    out = result.stderr  # ffmpeg writes astats to stderr
    peak_line = next((l for l in out.splitlines() if "Peak level dB" in l), None)
    max_line = next((l for l in out.splitlines() if "Max level" in l and "Peak" not in l), None)
    print(f"\n=== AUDIO INTEGRITY ===")
    print(f"  {peak_line}")
    print(f"  {max_line}")

    if peak_line:
        try:
            peak = float(peak_line.split(":")[-1].strip())
            if peak >= 0:
                print(f"\n!! WARNING: peak {peak} dB is at or above 0 — clipping not fully resolved")
            else:
                print(f"\nOK: peak {peak} dB is below 0 — no digital clipping")
        except ValueError:
            pass

    # Save script + timestamps for show notes phase
    timestamps_path = SCRIPT_PATH.with_name(f"{EPISODE_DATE}_timestamps.json")
    timestamps_path.write_text(json.dumps(timestamps, indent=2), encoding="utf-8")
    log.info(f"Wrote timestamps: {timestamps_path}")

    print(f"\nLocal MP3: {mp3_path}")
    print(f"Listen with: open '{mp3_path}'")
    print(f"Then run: python scripts/rerender_2026-04-25.py --phase publish")


def phase_publish():
    if not MP3_PATH.exists():
        sys.exit(f"Missing MP3 (run --phase synthesize first): {MP3_PATH}")

    weekly_html = WEEKLY_HTML_PATH.read_text(encoding="utf-8") if WEEKLY_HTML_PATH.exists() else ""

    # Generate show notes from the saved script + timestamps
    timestamps_path = SCRIPT_PATH.with_name(f"{EPISODE_DATE}_timestamps.json")
    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    timestamps = json.loads(timestamps_path.read_text(encoding="utf-8")) if timestamps_path.exists() else []

    duration_str = _get_duration_str(MP3_PATH)
    show_notes_md, show_notes_html = generate_show_notes(
        script, timestamps, EPISODE_DATE, weekly_html, duration_str,
    )
    log.info(f"Show notes: {len(show_notes_md)} chars markdown, {len(show_notes_html)} chars HTML")

    log.info("Publishing to GitHub release (--clobber)...")
    episode = publish_podcast(MP3_PATH, EPISODE_DATE, weekly_html, show_notes_html)
    if not episode:
        sys.exit("Publish failed")

    print(f"\nPublished episode #{episode.get('number')}: {episode.get('title')}")
    print(f"Duration: {episode.get('duration')}")
    print(f"MP3 URL: {episode.get('mp3_url')}")
    print(f"\nVerify on iPhone: https://www.thevalvewire.com/api/podcast/{EPISODE_DATE}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--phase", required=True, choices=["script", "synthesize", "publish"])
    args = p.parse_args()
    if args.phase == "script":
        phase_script()
    elif args.phase == "synthesize":
        phase_synthesize()
    elif args.phase == "publish":
        phase_publish()
