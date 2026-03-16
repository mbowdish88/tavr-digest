"""Generate professional podcast audio assets using OpenAI TTS and synthesized tones.

Run once to create intro/outro bumpers and transition stingers:
    python -m podcast.generate_assets

Assets are saved to static/audio/ and used by the assembler.
"""

from __future__ import annotations

import logging
import math
import struct
import wave
import io
from pathlib import Path

from pydub import AudioSegment

logger = logging.getLogger(__name__)


def _make_tone(freq: float, duration_ms: int, sample_rate: int = 44100) -> AudioSegment:
    """Generate a clean sine tone with smooth envelope."""
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    fade_ms = min(50, duration_ms // 4)
    fade_samples = int(sample_rate * fade_ms / 1000)

    for i in range(n_samples):
        t = i / sample_rate
        env = 1.0
        if i < fade_samples:
            env = i / fade_samples
        elif i > n_samples - fade_samples:
            env = (n_samples - i) / fade_samples
        sample = int(env * 6000 * math.sin(2 * math.pi * freq * t))
        samples.append(struct.pack('<h', max(-32768, min(32767, sample))))

    buf = io.BytesIO()
    with wave.open(buf, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(samples))
    buf.seek(0)
    return AudioSegment.from_wav(buf)


def _make_chord(freqs: list[float], duration_ms: int, sample_rate: int = 44100) -> AudioSegment:
    """Layer multiple tones into a chord."""
    chord = AudioSegment.silent(duration=duration_ms)
    for freq in freqs:
        tone = _make_tone(freq, duration_ms, sample_rate)
        chord = chord.overlay(tone)
    return chord


def generate_transition_stinger(output_path: Path):
    """Generate a clean, professional transition stinger (~1.2 seconds).

    Uses a rising major chord progression — subtle and broadcast-quality.
    """
    # C major arpeggio: C5 -> E5 -> G5 with gentle overlap
    c5 = _make_tone(523.25, 300)
    e5 = _make_tone(659.25, 300)
    g5 = _make_tone(783.99, 400)

    stinger = c5 + AudioSegment.silent(50) + e5 + AudioSegment.silent(50) + g5
    stinger = stinger.fade_in(80).fade_out(200) - 14  # Subtle volume
    stinger.export(str(output_path), format="mp3", bitrate="128k")
    logger.info(f"Transition stinger: {output_path.name} ({len(stinger) / 1000:.1f}s)")


def generate_intro_bed(output_path: Path):
    """Generate a professional intro music bed (~5 seconds).

    Warm ascending chord progression that resolves — signals "show starting."
    """
    # Warm pad: layer thirds for richness
    # C major -> F major -> G major -> C major (I-IV-V-I)
    chords = [
        ([261.63, 329.63, 392.00], 1200),  # C major
        ([349.23, 440.00, 523.25], 1000),  # F major
        ([392.00, 493.88, 587.33], 1000),  # G major
        ([523.25, 659.25, 783.99], 1500),  # C major (octave up, resolve)
    ]

    intro = AudioSegment.silent(duration=200)
    for freqs, dur in chords:
        chord = _make_chord(freqs, dur)
        chord = chord.fade_in(100).fade_out(150)
        intro += chord + AudioSegment.silent(80)

    intro = intro.fade_in(300).fade_out(800) - 10
    intro.export(str(output_path), format="mp3", bitrate="128k")
    logger.info(f"Intro bed: {output_path.name} ({len(intro) / 1000:.1f}s)")


def generate_outro_bed(output_path: Path):
    """Generate a professional outro music bed (~4 seconds).

    Descending resolution — signals "show ending."
    """
    chords = [
        ([523.25, 659.25, 783.99], 1200),  # C major (high)
        ([392.00, 493.88, 587.33], 1000),  # G major
        ([349.23, 440.00, 523.25], 1000),  # F major
        ([261.63, 329.63, 392.00], 1500),  # C major (resolve down)
    ]

    outro = AudioSegment.silent(duration=100)
    for freqs, dur in chords:
        chord = _make_chord(freqs, dur)
        chord = chord.fade_in(100).fade_out(200)
        outro += chord + AudioSegment.silent(80)

    outro = outro.fade_in(500).fade_out(1200) - 10
    outro.export(str(output_path), format="mp3", bitrate="128k")
    logger.info(f"Outro bed: {output_path.name} ({len(outro) / 1000:.1f}s)")


def generate_cold_open_leadin(output_path: Path):
    """Generate the 'Coming up on The Valve Wire Weekly...' lead-in via TTS."""
    try:
        from openai import OpenAI
        import config

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.audio.speech.create(
            model=config.OPENAI_TTS_MODEL,
            voice=config.PODCAST_HOST_A_VOICE,
            input="Coming up on The Valve Wire Weekly...",
            response_format="mp3",
            speed=0.95,
        )
        response.stream_to_file(str(output_path))
        logger.info(f"Cold open lead-in: {output_path.name}")
    except Exception as e:
        logger.warning(f"Could not generate TTS lead-in (will work without it): {e}")


def generate_all_assets():
    """Generate all podcast audio assets."""
    import config

    audio_dir = config.PODCAST_AUDIO_DIR
    audio_dir.mkdir(parents=True, exist_ok=True)

    print("Generating podcast audio assets...")

    generate_intro_bed(audio_dir / "intro.mp3")
    generate_transition_stinger(audio_dir / "transition.mp3")
    generate_outro_bed(audio_dir / "outro.mp3")
    generate_cold_open_leadin(audio_dir / "cold_open_leadin.mp3")

    print(f"All assets saved to {audio_dir}/")
    print("Tip: Replace these with professionally produced audio for best results.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_all_assets()
