"""Synthesize podcast script segments into audio files using OpenAI TTS."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from openai import OpenAI
from pydub import AudioSegment

import config

logger = logging.getLogger(__name__)


def synthesize_segments(script: list[dict], episode_date: str) -> list[dict]:
    """Synthesize each script segment into an individual audio file.

    Args:
        script: List of script segment dicts with speaker, text, section.
        episode_date: Date string for organizing files (e.g., "2026-03-14").

    Returns:
        List of dicts with segment info and audio file path.
    """
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    segments_dir = config.PODCAST_SEGMENTS_DIR / episode_date
    segments_dir.mkdir(parents=True, exist_ok=True)

    voice_map = {
        "A": config.PODCAST_HOST_A_VOICE,
        "B": config.PODCAST_HOST_B_VOICE,
    }

    results = []
    total = len(script)

    for i, segment in enumerate(script):
        voice = voice_map.get(segment["speaker"], config.PODCAST_HOST_A_VOICE)
        filepath = segments_dir / f"{i:03d}_{segment['speaker']}_{segment.get('section', 'unknown')}.mp3"

        # Skip if already synthesized (resume support)
        if filepath.exists() and filepath.stat().st_size > 0:
            logger.debug(f"Segment {i}/{total} already exists, skipping")
            results.append({**segment, "audio_path": filepath})
            continue

        logger.info(f"Synthesizing segment {i + 1}/{total} ({segment['speaker']}, {len(segment['text'])} chars)")

        # Retry with exponential backoff on failure
        max_retries = 3
        success = False
        for attempt in range(max_retries):
            try:
                response = client.audio.speech.create(
                    model=config.OPENAI_TTS_MODEL,
                    voice=voice,
                    input=segment["text"],
                    response_format="mp3",
                    speed=1.0,
                    timeout=120.0,
                )
                response.stream_to_file(str(filepath))

                # Post-process for broadcast quality
                from podcast.audio_processing import process_voice_segment
                raw_audio = AudioSegment.from_mp3(str(filepath))
                processed = process_voice_segment(raw_audio)
                processed.export(str(filepath), format="mp3", bitrate="192k")

                results.append({**segment, "audio_path": filepath})
                success = True
                break

            except Exception as e:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.error(
                    f"Failed to synthesize segment {i} (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {wait}s...")
                    time.sleep(wait)

        if not success:
            results.append({**segment, "audio_path": None})

        # Brief pause between API calls
        if i < total - 1:
            time.sleep(0.2)

    successful = sum(1 for r in results if r.get("audio_path"))
    logger.info(f"Synthesized {successful}/{total} segments to {segments_dir}")

    return results
