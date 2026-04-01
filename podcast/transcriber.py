"""Transcribe podcast episodes using OpenAI Whisper API."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 25


def transcribe_episode(mp3_path: Path) -> dict:
    """Transcribe a podcast episode using Whisper.

    Args:
        mp3_path: Path to the MP3 file.

    Returns:
        Dict with 'text' (full transcript) and 'segments' (timestamped segments).
    """
    file_size_mb = mp3_path.stat().st_size / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        logger.warning(
            f"File is {file_size_mb:.1f}MB, exceeds Whisper {MAX_FILE_SIZE_MB}MB limit. "
            f"Transcribing in chunks."
        )
        return _transcribe_chunked(mp3_path)

    client = OpenAI(api_key=config.OPENAI_API_KEY)

    logger.info(f"Transcribing {mp3_path.name} ({file_size_mb:.1f}MB)")

    with open(mp3_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            timeout=300.0,
        )

    result = {
        "text": response.text,
        "segments": [
            {
                "start": getattr(seg, "start", 0),
                "end": getattr(seg, "end", 0),
                "text": getattr(seg, "text", ""),
            }
            for seg in (response.segments or [])
        ],
    }

    logger.info(f"Transcription complete: {len(result['text'])} chars, {len(result['segments'])} segments")

    # Save files
    episode_date = mp3_path.stem.split("_")[0]  # Extract date from filename

    # Plain text
    txt_path = config.PODCAST_DIR / f"{episode_date}_transcript.txt"
    txt_path.write_text(result["text"], encoding="utf-8")

    # JSON with timestamps
    json_path = config.PODCAST_DIR / f"{episode_date}_transcript.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # WebVTT for web players
    vtt_path = config.PODCAST_DIR / f"{episode_date}_transcript.vtt"
    vtt_path.write_text(_to_vtt(result["segments"]), encoding="utf-8")

    logger.info(f"Saved transcript: {txt_path.name}, {json_path.name}, {vtt_path.name}")

    return result


def _transcribe_chunked(mp3_path: Path) -> dict:
    """Transcribe a large file by splitting into chunks."""
    from pydub import AudioSegment

    audio = AudioSegment.from_mp3(str(mp3_path))
    chunk_duration_ms = 10 * 60 * 1000  # 10-minute chunks
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    all_text = []
    all_segments = []
    offset_secs = 0

    for i in range(0, len(audio), chunk_duration_ms):
        chunk = audio[i:i + chunk_duration_ms]
        chunk_path = mp3_path.parent / f"_chunk_{i // chunk_duration_ms}.mp3"
        chunk.export(str(chunk_path), format="mp3", bitrate="128k")

        logger.info(f"Transcribing chunk {i // chunk_duration_ms + 1}")

        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
                timeout=300.0,
            )

        all_text.append(response.text)
        for seg in (response.segments or []):
            all_segments.append({
                "start": getattr(seg, "start", 0) + offset_secs,
                "end": getattr(seg, "end", 0) + offset_secs,
                "text": getattr(seg, "text", ""),
            })

        offset_secs += len(chunk) / 1000
        chunk_path.unlink()  # Clean up

    result = {"text": " ".join(all_text), "segments": all_segments}

    # Save files
    episode_date = mp3_path.stem.split("_")[0]
    txt_path = config.PODCAST_DIR / f"{episode_date}_transcript.txt"
    txt_path.write_text(result["text"], encoding="utf-8")
    json_path = config.PODCAST_DIR / f"{episode_date}_transcript.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    vtt_path = config.PODCAST_DIR / f"{episode_date}_transcript.vtt"
    vtt_path.write_text(_to_vtt(result["segments"]), encoding="utf-8")

    logger.info(f"Chunked transcription complete: {len(result['text'])} chars")
    return result


def _to_vtt(segments: list[dict]) -> str:
    """Convert segments to WebVTT format."""
    lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments):
        start = _format_vtt_time(seg["start"])
        end = _format_vtt_time(seg["end"])
        text = seg["text"].strip()
        if text:
            lines.append(str(i + 1))
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
    return "\n".join(lines)


def _format_vtt_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm for WebVTT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
