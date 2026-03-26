"""Assemble synthesized audio segments into a polished podcast MP3."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from pydub import AudioSegment
from pydub.effects import compress_dynamic_range
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC

import config

logger = logging.getLogger(__name__)

# Timing constants (milliseconds)
COLD_OPEN_DURATION = 15000         # 15-second teaser clip
COLD_OPEN_PAUSE = 800              # Pause after cold open before intro
PAUSE_SAME_SPEAKER = 250           # Brief pause between same-speaker segments
PAUSE_SPEAKER_SWITCH = 600         # Pause when switching speakers
INTRO_FADE_OUT = 3500              # Intro music fade-out duration
OUTRO_FADE_IN = 3000               # Outro music fade-in duration
TRANSITION_CROSSFADE = 150         # Crossfade into transition stingers
BG_MUSIC_DB = -28                  # Background music volume reduction
BG_MUSIC_CUTOFF_HZ = 3500         # Low-pass cutoff for background music


def _load_audio_asset(name: str) -> AudioSegment:
    """Load a static audio asset, return None if not found."""
    filepath = config.PODCAST_AUDIO_DIR / name
    if not filepath.exists():
        logger.debug(f"Audio asset not found: {name}")
        return None
    return AudioSegment.from_file(str(filepath))


def _generate_placeholder_tones():
    """Generate simple tone-based placeholders for intro/transition/outro."""
    import math
    import struct
    import wave
    import io

    def _make_tone(freq, duration_ms, sample_rate=44100):
        n_samples = int(sample_rate * duration_ms / 1000)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
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

    intro = _make_tone(523, 1500) + AudioSegment.silent(200) + _make_tone(659, 1500)
    intro = intro.fade_in(500).fade_out(500) - 10

    transition = _make_tone(440, 400) + _make_tone(554, 400) + _make_tone(659, 400)
    transition = transition.fade_in(100).fade_out(200) - 12

    outro = _make_tone(659, 1000) + _make_tone(554, 1000) + _make_tone(440, 1500)
    outro = outro.fade_in(300).fade_out(800) - 10

    return intro, transition, outro


def _build_cold_open(segments: list[dict], lead_in_path: Path = None) -> AudioSegment:
    """Build a cold open teaser from a compelling segment.

    Extracts a 15-second clip from a content segment and prepends
    a "Coming up on The Valve Wire Weekly..." lead-in.
    """
    # Find a compelling segment from content sections (not intro/closing)
    content_sections = {"top_stories", "aortic", "mitral", "tricuspid", "trials", "market"}
    candidates = [
        s for s in segments
        if s.get("section") in content_sections and s.get("audio_path")
    ]

    if not candidates:
        return AudioSegment.silent(duration=100)

    # Pick the longest segment (tends to be most substantive)
    best = max(candidates, key=lambda s: len(s.get("text", "")))

    try:
        clip_audio = AudioSegment.from_mp3(str(best["audio_path"]))
    except Exception:
        return AudioSegment.silent(duration=100)

    # Trim to 15 seconds max
    if len(clip_audio) > COLD_OPEN_DURATION:
        clip_audio = clip_audio[:COLD_OPEN_DURATION]
    clip_audio = clip_audio.fade_in(200).fade_out(500)

    # Load or generate lead-in
    lead_in = None
    if lead_in_path and lead_in_path.exists():
        lead_in = AudioSegment.from_file(str(lead_in_path))

    cold_open = AudioSegment.silent(duration=300)
    if lead_in:
        cold_open += lead_in + AudioSegment.silent(duration=400)
    cold_open += clip_audio
    cold_open += AudioSegment.silent(duration=COLD_OPEN_PAUSE)

    logger.info(f"Cold open: {len(cold_open) / 1000:.1f}s teaser from '{best.get('section')}'")
    return cold_open


def assemble_podcast(
    segments: list[dict],
    episode_date: str,
    title: str = None,
) -> tuple[Path, list[dict]]:
    """Assemble individual audio segments into a complete podcast episode.

    Args:
        segments: List of segment dicts with audio_path, speaker, section.
        episode_date: Date string (e.g., "2026-03-14").
        title: Episode title for ID3 tags.

    Returns:
        Tuple of (path to final MP3, list of section timestamp dicts).
    """
    logger.info(f"Assembling podcast from {len(segments)} segments")

    # Load audio assets (use placeholders if missing)
    intro_music = _load_audio_asset("intro.wav") or _load_audio_asset("intro.mp3")
    transition_sound = _load_audio_asset("transition.wav") or _load_audio_asset("transition.mp3")
    outro_music = _load_audio_asset("outro.wav") or _load_audio_asset("outro.mp3")
    bg_music = _load_audio_asset("background.wav") or _load_audio_asset("background.mp3")
    lead_in = config.PODCAST_AUDIO_DIR / "cold_open_leadin.mp3"

    if not intro_music:
        logger.info("No audio assets found, generating assets on first run")
        from podcast.generate_assets import generate_all_assets
        generate_all_assets()
        # Reload after generation
        intro_music = _load_audio_asset("intro.wav") or _load_audio_asset("intro.mp3")
        transition_sound = _load_audio_asset("transition.wav") or _load_audio_asset("transition.mp3")
        outro_music = _load_audio_asset("outro.wav") or _load_audio_asset("outro.mp3")
        bg_music = _load_audio_asset("background.wav") or _load_audio_asset("background.mp3")
    if not intro_music:
        logger.warning("Asset generation failed, using placeholder tones")
        intro_music, transition_sound, outro_music = _generate_placeholder_tones()
    if not transition_sound:
        transition_sound = AudioSegment.silent(duration=800)

    # === Phase 1: Cold Open ===
    cold_open = _build_cold_open(segments, lead_in if lead_in.exists() else None)
    podcast = cold_open

    # === Phase 2: Intro Music ===
    podcast += intro_music.fade_out(INTRO_FADE_OUT)
    podcast += AudioSegment.silent(duration=500)

    voice_start_ms = len(podcast)  # Track where voice content begins (for bg music)
    timestamps = []
    prev_speaker = None
    prev_section = None

    # === Phase 3: Voice Segments ===
    for i, seg in enumerate(segments):
        if seg.get("audio_path") is None:
            continue

        try:
            audio = AudioSegment.from_mp3(str(seg["audio_path"]))
        except Exception as e:
            logger.warning(f"Failed to load segment {i}: {e}")
            continue

        current_section = seg.get("section", "")
        current_speaker = seg["speaker"]

        # Track section timestamps
        if current_section and current_section != prev_section:
            timestamps.append({
                "section": current_section,
                "offset_ms": len(podcast),
            })

        # Section transition — crossfade into stinger
        if prev_section and current_section != prev_section and current_section not in ("", prev_section):
            if transition_sound:
                podcast = podcast.append(transition_sound, crossfade=TRANSITION_CROSSFADE)
            podcast += AudioSegment.silent(duration=200)
        elif prev_speaker and current_speaker != prev_speaker:
            podcast += AudioSegment.silent(duration=PAUSE_SPEAKER_SWITCH)
        elif prev_speaker:
            podcast += AudioSegment.silent(duration=PAUSE_SAME_SPEAKER)

        podcast += audio
        prev_speaker = current_speaker
        prev_section = current_section

    voice_end_ms = len(podcast)  # Track where voice content ends

    # === Phase 4: Outro ===
    podcast += AudioSegment.silent(duration=800)
    if outro_music:
        podcast += outro_music.fade_in(OUTRO_FADE_IN)
    else:
        _, _, outro_placeholder = _generate_placeholder_tones()
        podcast += outro_placeholder.fade_in(OUTRO_FADE_IN)

    # === Phase 5: Background Music Bed ===
    if bg_music and voice_start_ms < voice_end_ms:
        voice_duration = voice_end_ms - voice_start_ms
        # Loop background music to cover the voice section
        loops_needed = (voice_duration // len(bg_music)) + 1
        bg_looped = bg_music * loops_needed
        bg_looped = bg_looped[:voice_duration]
        # Low-pass filter so background doesn't compete with voice frequencies
        bg_looped = bg_looped.low_pass_filter(BG_MUSIC_CUTOFF_HZ)
        bg_looped = bg_looped + BG_MUSIC_DB
        bg_looped = bg_looped.fade_in(3000).fade_out(5000)

        # Overlay under the voice sections only
        podcast = podcast.overlay(bg_looped, position=voice_start_ms)
        logger.info(f"Background music: overlaid {voice_duration / 1000:.0f}s at {BG_MUSIC_DB}dB, LP {BG_MUSIC_CUTOFF_HZ}Hz")

    # === Phase 6: Final Compression + Loudness Normalization ===
    # Gentle bus compression to glue the mix together
    podcast = compress_dynamic_range(
        podcast,
        threshold=-18.0,
        ratio=2.0,
        attack=10.0,
        release=100.0,
    )
    # Normalize to broadcast target loudness
    target_dBFS = -16.0
    change = target_dBFS - podcast.dBFS
    podcast = podcast.apply_gain(change)

    # === Phase 7: Export ===
    output_filename = f"{episode_date}_valve_wire_weekly.mp3"
    output_path = config.PODCAST_DIR / output_filename
    podcast.export(
        str(output_path),
        format="mp3",
        bitrate="192k",
        parameters=["-ac", "1"],
    )

    # === Phase 8: ID3 Tags + Cover Art ===
    try:
        audio_file = MP3(str(output_path), ID3=ID3)
        if audio_file.tags is None:
            audio_file.add_tags()
        audio_file.tags.add(TIT2(encoding=3, text=[title or f"The Valve Wire Weekly - {episode_date}"]))
        audio_file.tags.add(TPE1(encoding=3, text=["E. Nolan Beckett, MD & Claire Marchand, MBA"]))
        audio_file.tags.add(TALB(encoding=3, text=["The Valve Wire Weekly"]))
        audio_file.tags.add(TDRC(encoding=3, text=[episode_date[:4]]))
        audio_file.tags.add(TCON(encoding=3, text=["Science & Medicine"]))

        # Embed cover art if available (convert SVG to PNG if needed)
        cover_png = config.BASE_DIR / "static" / "podcast-cover.png"
        cover_svg = config.BASE_DIR / "static" / "podcast-cover.svg"
        if not cover_png.exists() and cover_svg.exists():
            try:
                import cairosvg
                cairosvg.svg2png(
                    url=str(cover_svg),
                    write_to=str(cover_png),
                    output_width=3000,
                    output_height=3000,
                )
                logger.info("Converted podcast-cover.svg to PNG (3000x3000)")
            except ImportError:
                logger.warning("cairosvg not installed — cannot convert SVG cover to PNG")
            except Exception as e:
                logger.warning(f"SVG to PNG conversion failed: {e}")

        if cover_png.exists():
            with open(cover_png, 'rb') as f:
                audio_file.tags.add(APIC(
                    encoding=3, mime='image/png', type=3,
                    desc='Cover', data=f.read(),
                ))
            logger.info("Embedded cover art in MP3")

        audio_file.save()
    except Exception as e:
        logger.warning(f"Failed to add ID3 tags: {e}")

    duration_secs = len(podcast) / 1000
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(
        f"Podcast assembled: {output_path.name} "
        f"({duration_secs / 60:.1f} min, {file_size_mb:.1f} MB)"
    )

    return output_path, timestamps
