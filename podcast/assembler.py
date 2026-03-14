"""Assemble synthesized audio segments into a polished podcast MP3."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from pydub import AudioSegment
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON

import config

logger = logging.getLogger(__name__)

# Timing constants (milliseconds)
PAUSE_SAME_SPEAKER = 250       # Brief pause between consecutive same-speaker segments
PAUSE_SPEAKER_SWITCH = 600     # Pause when switching speakers
PAUSE_SECTION_CHANGE = 100     # Short pause before transition stinger plays
CROSSFADE_DURATION = 80        # Crossfade between segments
INTRO_FADE_OUT = 2500          # Intro music fade-out duration
OUTRO_FADE_IN = 2000           # Outro music fade-in duration
TRANSITION_CROSSFADE = 200     # Crossfade around transition stingers


def _load_audio_asset(name: str) -> AudioSegment:
    """Load a static audio asset (intro, transition, outro)."""
    filepath = config.PODCAST_AUDIO_DIR / name
    if not filepath.exists():
        logger.warning(f"Audio asset not found: {filepath}, generating silence")
        # Generate appropriate silence as placeholder
        if "intro" in name:
            return AudioSegment.silent(duration=3000)
        elif "transition" in name:
            return AudioSegment.silent(duration=1500)
        elif "outro" in name:
            return AudioSegment.silent(duration=3000)
        return AudioSegment.silent(duration=1000)

    return AudioSegment.from_file(str(filepath))


def _generate_placeholder_tones():
    """Generate simple tone-based placeholders for intro/transition/outro.

    These are functional placeholders. Replace with real music later.
    """
    import math
    import struct
    import wave
    import io

    def _make_tone(freq, duration_ms, sample_rate=44100):
        """Generate a sine wave tone."""
        n_samples = int(sample_rate * duration_ms / 1000)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            # Fade in/out envelope
            env = 1.0
            fade_samples = int(sample_rate * 0.1)
            if i < fade_samples:
                env = i / fade_samples
            elif i > n_samples - fade_samples:
                env = (n_samples - i) / fade_samples
            sample = int(env * 8000 * math.sin(2 * math.pi * freq * t))
            samples.append(struct.pack('<h', max(-32768, min(32767, sample))))

        buf = io.BytesIO()
        with wave.open(buf, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(samples))
        buf.seek(0)
        return AudioSegment.from_wav(buf)

    # Intro: two-note chime (C5 + E5)
    intro = _make_tone(523, 1500) + AudioSegment.silent(200) + _make_tone(659, 1500)
    intro = intro.fade_in(500).fade_out(500) - 10  # Reduce volume

    # Transition: quick ascending tone
    transition = _make_tone(440, 400) + _make_tone(554, 400) + _make_tone(659, 400)
    transition = transition.fade_in(100).fade_out(200) - 12

    # Outro: descending tones
    outro = _make_tone(659, 1000) + _make_tone(554, 1000) + _make_tone(440, 1500)
    outro = outro.fade_in(300).fade_out(800) - 10

    return intro, transition, outro


def assemble_podcast(
    segments: list[dict],
    episode_date: str,
    title: str = None,
) -> Path:
    """Assemble individual audio segments into a complete podcast episode.

    Args:
        segments: List of segment dicts with audio_path, speaker, section.
        episode_date: Date string (e.g., "2026-03-14").
        title: Episode title for ID3 tags.

    Returns:
        Path to the final MP3 file.
    """
    logger.info(f"Assembling podcast from {len(segments)} segments")

    # Load or generate audio assets
    intro_music = _load_audio_asset("intro.mp3")
    transition_sound = _load_audio_asset("transition.mp3")
    outro_music = _load_audio_asset("outro.mp3")

    # If assets are placeholders (silent), generate tones
    if intro_music.dBFS == float('-inf'):
        logger.info("No audio assets found, generating placeholder tones")
        intro_music, transition_sound, outro_music = _generate_placeholder_tones()

    # Start with intro music
    podcast = intro_music.fade_out(INTRO_FADE_OUT)
    podcast += AudioSegment.silent(duration=500)

    prev_speaker = None
    prev_section = None

    for i, seg in enumerate(segments):
        if seg.get("audio_path") is None:
            logger.warning(f"Skipping segment {i} (no audio)")
            continue

        try:
            audio = AudioSegment.from_mp3(str(seg["audio_path"]))
        except Exception as e:
            logger.warning(f"Failed to load segment {i}: {e}")
            continue

        current_section = seg.get("section", "")
        current_speaker = seg["speaker"]

        # Section transition — insert stinger
        if prev_section and current_section != prev_section and current_section not in ("", prev_section):
            podcast += AudioSegment.silent(duration=PAUSE_SECTION_CHANGE)
            podcast += transition_sound
            podcast += AudioSegment.silent(duration=PAUSE_SECTION_CHANGE)

        # Speaker transition pause
        elif prev_speaker and current_speaker != prev_speaker:
            podcast += AudioSegment.silent(duration=PAUSE_SPEAKER_SWITCH)

        # Same speaker continuation
        elif prev_speaker:
            podcast += AudioSegment.silent(duration=PAUSE_SAME_SPEAKER)

        # Append the audio segment
        podcast += audio

        prev_speaker = current_speaker
        prev_section = current_section

    # Add outro
    podcast += AudioSegment.silent(duration=800)
    podcast += outro_music.fade_in(OUTRO_FADE_IN)

    # Normalize volume
    target_dBFS = -16.0
    change = target_dBFS - podcast.dBFS
    podcast = podcast.apply_gain(change)

    # Export
    output_filename = f"{episode_date}_valve_wire_weekly.mp3"
    output_path = config.PODCAST_DIR / output_filename
    podcast.export(
        str(output_path),
        format="mp3",
        bitrate="128k",
        parameters=["-ac", "1"],  # Mono (voice-optimized)
    )

    # Add ID3 tags
    try:
        audio_file = MP3(str(output_path), ID3=ID3)
        if audio_file.tags is None:
            audio_file.add_tags()
        audio_file.tags.add(TIT2(encoding=3, text=[title or f"The Valve Wire Weekly - {episode_date}"]))
        audio_file.tags.add(TPE1(encoding=3, text=["E. Nolan Beckett"]))
        audio_file.tags.add(TALB(encoding=3, text=["The Valve Wire Weekly"]))
        audio_file.tags.add(TDRC(encoding=3, text=[episode_date[:4]]))
        audio_file.tags.add(TCON(encoding=3, text=["Science & Medicine"]))
        audio_file.save()
    except Exception as e:
        logger.warning(f"Failed to add ID3 tags: {e}")

    duration_secs = len(podcast) / 1000
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(
        f"Podcast assembled: {output_path.name} "
        f"({duration_secs / 60:.1f} min, {file_size_mb:.1f} MB)"
    )

    return output_path
