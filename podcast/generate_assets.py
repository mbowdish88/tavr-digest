"""Generate professional podcast audio assets using numpy additive synthesis.

Uses layered oscillators with harmonics, ADSR envelopes, detuned chorus pads,
and convolution reverb to create warm, broadcast-quality music beds and stingers.

Run once to create/refresh all assets:
    python -m podcast.generate_assets

Assets are saved to static/audio/ and used by the assembler.
"""

from __future__ import annotations

import io
import logging
import wave
from pathlib import Path

import numpy as np
from pydub import AudioSegment

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100


# ---------------------------------------------------------------------------
# Core synthesis primitives
# ---------------------------------------------------------------------------

def _oscillator(freq: float, duration_s: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Generate a rich oscillator with harmonic partials.

    Sums fundamental + 4 harmonics with decreasing amplitude for a warm,
    organ-like timbre that is far richer than a bare sine wave.
    """
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
    # Harmonic series with natural rolloff
    harmonics = [
        (1.0, 1),    # fundamental
        (0.5, 2),    # octave
        (0.25, 3),   # fifth above octave
        (0.12, 4),   # two octaves
        (0.06, 5),   # major third above two octaves
    ]
    signal = np.zeros_like(t)
    for amplitude, multiple in harmonics:
        signal += amplitude * np.sin(2 * np.pi * freq * multiple * t)
    # Normalize to [-1, 1]
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal /= peak
    return signal


def _adsr_envelope(
    n_samples: int,
    attack_s: float = 0.1,
    decay_s: float = 0.2,
    sustain_level: float = 0.6,
    release_s: float = 0.3,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Generate an ADSR amplitude envelope."""
    attack = int(attack_s * sr)
    decay = int(decay_s * sr)
    release = int(release_s * sr)
    sustain = max(0, n_samples - attack - decay - release)

    env = np.concatenate([
        np.linspace(0, 1, attack, endpoint=False),                    # Attack
        np.linspace(1, sustain_level, decay, endpoint=False),          # Decay
        np.full(sustain, sustain_level),                               # Sustain
        np.linspace(sustain_level, 0, release, endpoint=False),        # Release
    ])
    # Pad or trim to exact length
    if len(env) < n_samples:
        env = np.concatenate([env, np.zeros(n_samples - len(env))])
    return env[:n_samples]


def _detune_pad(
    freq: float,
    duration_s: float,
    n_voices: int = 5,
    detune_cents: float = 8.0,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Create a lush pad by layering detuned oscillators (chorus effect).

    Each voice is offset by a fraction of `detune_cents` cents from the
    center frequency, creating a rich, shimmering texture.
    """
    n_samples = int(sr * duration_s)
    pad = np.zeros(n_samples)
    for i in range(n_voices):
        # Spread voices evenly across the detune range
        offset = (i - (n_voices - 1) / 2) * (detune_cents / (n_voices - 1)) if n_voices > 1 else 0
        voice_freq = freq * (2 ** (offset / 1200))
        pad += _oscillator(voice_freq, duration_s, sr)
    pad /= n_voices
    return pad


def _simple_reverb(
    signal: np.ndarray,
    decay_s: float = 1.5,
    wet: float = 0.3,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Apply convolution reverb using a synthetic exponential-decay impulse.

    Args:
        signal: Input signal array.
        decay_s: Reverb tail length in seconds.
        wet: Wet/dry mix (0 = fully dry, 1 = fully wet).
        sr: Sample rate.
    """
    ir_length = int(decay_s * sr)
    t = np.linspace(0, decay_s, ir_length, endpoint=False)
    # Exponentially decaying noise impulse response
    rng = np.random.default_rng(42)  # deterministic for reproducibility
    ir = rng.normal(0, 1, ir_length) * np.exp(-3.0 * t / decay_s)
    ir /= np.max(np.abs(ir))

    # Convolve and trim to original length
    reverbed = np.convolve(signal, ir, mode="full")[:len(signal)]
    reverbed /= max(np.max(np.abs(reverbed)), 1e-6)

    # Mix dry + wet
    mixed = (1 - wet) * signal + wet * reverbed
    peak = np.max(np.abs(mixed))
    if peak > 0:
        mixed /= peak
    return mixed


def _to_audio_segment(signal: np.ndarray, sr: int = SAMPLE_RATE) -> AudioSegment:
    """Convert a float numpy array [-1..1] to a pydub AudioSegment."""
    # Clip and convert to 16-bit PCM
    signal = np.clip(signal, -1.0, 1.0)
    pcm = (signal * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    buf.seek(0)
    return AudioSegment.from_wav(buf)


def _make_pad_note(
    freq: float,
    duration_s: float,
    attack_s: float = 0.5,
    decay_s: float = 0.3,
    sustain_level: float = 0.6,
    release_s: float = 1.0,
    reverb_s: float = 1.5,
    reverb_wet: float = 0.3,
) -> np.ndarray:
    """Generate a complete pad note: detuned oscillators + ADSR + reverb."""
    n_samples = int(SAMPLE_RATE * duration_s)
    pad = _detune_pad(freq, duration_s)
    env = _adsr_envelope(n_samples, attack_s, decay_s, sustain_level, release_s)
    shaped = pad * env
    return _simple_reverb(shaped, reverb_s, reverb_wet)


# ---------------------------------------------------------------------------
# Asset generators
# ---------------------------------------------------------------------------

def generate_intro_bed(output_path: Path):
    """Generate a warm, professional intro music bed (~8 seconds).

    Layered C major pad with a second voice entering mid-way.
    Warm low register, evolving texture, spacious reverb.
    """
    duration = 8.0

    # Layer 1: C3 major pad (C3=130.81, E3=164.81, G3=196.00)
    c3 = _make_pad_note(130.81, duration, attack_s=2.0, decay_s=0.5, sustain_level=0.5, release_s=2.5, reverb_s=2.0, reverb_wet=0.35)
    e3 = _make_pad_note(164.81, duration, attack_s=2.2, decay_s=0.5, sustain_level=0.45, release_s=2.5, reverb_s=2.0, reverb_wet=0.35)
    g3 = _make_pad_note(196.00, duration, attack_s=2.4, decay_s=0.5, sustain_level=0.4, release_s=2.5, reverb_s=2.0, reverb_wet=0.35)

    layer1 = 0.4 * c3 + 0.3 * e3 + 0.3 * g3

    # Layer 2: Fifth above (G3, B3, D4) entering at t=3s, quieter
    n_samples = int(SAMPLE_RATE * duration)
    delay_samples = int(SAMPLE_RATE * 3.0)
    remaining = duration - 3.0

    g3b = _make_pad_note(196.00, remaining, attack_s=2.0, decay_s=0.3, sustain_level=0.4, release_s=2.0, reverb_s=2.0, reverb_wet=0.4)
    b3 = _make_pad_note(246.94, remaining, attack_s=2.2, decay_s=0.3, sustain_level=0.35, release_s=2.0, reverb_s=2.0, reverb_wet=0.4)
    d4 = _make_pad_note(293.66, remaining, attack_s=2.4, decay_s=0.3, sustain_level=0.3, release_s=2.0, reverb_s=2.0, reverb_wet=0.4)

    layer2_short = 0.35 * g3b + 0.35 * b3 + 0.3 * d4
    layer2 = np.zeros(n_samples)
    end = min(delay_samples + len(layer2_short), n_samples)
    layer2[delay_samples:end] = layer2_short[:end - delay_samples]

    # Mix layers
    mixed = 0.65 * layer1 + 0.35 * layer2
    peak = np.max(np.abs(mixed))
    if peak > 0:
        mixed /= peak

    audio = _to_audio_segment(mixed)
    audio = audio.fade_in(1500).fade_out(2000) - 8  # Slightly below full volume
    audio.export(str(output_path), format="mp3", bitrate="192k")
    logger.info(f"Intro bed: {output_path.name} ({len(audio) / 1000:.1f}s)")


def generate_outro_bed(output_path: Path):
    """Generate a resolving outro music bed (~6 seconds).

    Descending pad from higher to lower register with long release.
    """
    duration = 6.0
    n_samples = int(SAMPLE_RATE * duration)

    # Start with C4 major chord, morph down to C3
    # High chord (fades out over first 4s)
    c4 = _make_pad_note(261.63, 4.5, attack_s=0.3, decay_s=0.3, sustain_level=0.5, release_s=3.0, reverb_s=2.5, reverb_wet=0.4)
    e4 = _make_pad_note(329.63, 4.5, attack_s=0.4, decay_s=0.3, sustain_level=0.45, release_s=3.0, reverb_s=2.5, reverb_wet=0.4)
    g4 = _make_pad_note(392.00, 4.5, attack_s=0.5, decay_s=0.3, sustain_level=0.4, release_s=3.0, reverb_s=2.5, reverb_wet=0.4)

    high_chord = 0.4 * c4 + 0.3 * e4 + 0.3 * g4
    high_padded = np.zeros(n_samples)
    high_padded[:len(high_chord)] = high_chord

    # Low chord (fades in from t=1.5s)
    low_dur = duration - 1.5
    c3 = _make_pad_note(130.81, low_dur, attack_s=2.0, decay_s=0.5, sustain_level=0.5, release_s=2.5, reverb_s=2.5, reverb_wet=0.4)
    e3 = _make_pad_note(164.81, low_dur, attack_s=2.2, decay_s=0.5, sustain_level=0.45, release_s=2.5, reverb_s=2.5, reverb_wet=0.4)
    g3 = _make_pad_note(196.00, low_dur, attack_s=2.4, decay_s=0.5, sustain_level=0.4, release_s=2.5, reverb_s=2.5, reverb_wet=0.4)

    low_chord = 0.4 * c3 + 0.3 * e3 + 0.3 * g3
    delay = int(SAMPLE_RATE * 1.5)
    low_padded = np.zeros(n_samples)
    end = min(delay + len(low_chord), n_samples)
    low_padded[delay:end] = low_chord[:end - delay]

    # Crossfade: high fades out, low fades in
    mixed = 0.55 * high_padded + 0.45 * low_padded
    peak = np.max(np.abs(mixed))
    if peak > 0:
        mixed /= peak

    audio = _to_audio_segment(mixed)
    audio = audio.fade_in(500).fade_out(2500) - 8
    audio.export(str(output_path), format="mp3", bitrate="192k")
    logger.info(f"Outro bed: {output_path.name} ({len(audio) / 1000:.1f}s)")


def generate_transition_stinger(output_path: Path):
    """Generate a subtle, professional transition stinger (~1.2 seconds).

    Two quick detuned pad notes (G4 -> C5) with short reverb.
    """
    # Note 1: G4 (392 Hz), quick
    n1 = _make_pad_note(
        392.00, 0.5,
        attack_s=0.05, decay_s=0.1, sustain_level=0.5, release_s=0.25,
        reverb_s=0.8, reverb_wet=0.25,
    )
    # Note 2: C5 (523.25 Hz), slightly longer resolve
    n2 = _make_pad_note(
        523.25, 0.7,
        attack_s=0.05, decay_s=0.1, sustain_level=0.4, release_s=0.4,
        reverb_s=0.8, reverb_wet=0.25,
    )

    # Concatenate with small gap
    gap = np.zeros(int(SAMPLE_RATE * 0.05))
    stinger = np.concatenate([n1, gap, n2])

    audio = _to_audio_segment(stinger)
    audio = audio.fade_in(30).fade_out(150) - 14  # Keep it subtle
    audio.export(str(output_path), format="mp3", bitrate="192k")
    logger.info(f"Transition stinger: {output_path.name} ({len(audio) / 1000:.1f}s)")


def generate_background_music(output_path: Path):
    """Generate a loopable ambient background music bed (~45 seconds).

    Subtle evolving drone with slow LFO modulation. Designed to sit
    far behind voice without competing.
    """
    duration = 45.0
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)

    # Main drone: C3 pad with slow evolution
    drone_c3 = _detune_pad(130.81, duration, n_voices=5, detune_cents=12)

    # LFO amplitude modulation — one cycle every 20 seconds
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.05 * t)
    drone_c3 *= lfo

    # Secondary: barely-audible G3 fifth
    drone_g3 = _detune_pad(196.00, duration, n_voices=3, detune_cents=10)
    # Offset LFO for movement
    lfo2 = 0.6 + 0.4 * np.sin(2 * np.pi * 0.033 * t + 1.0)
    drone_g3 *= lfo2

    # Tertiary: very quiet octave C4 shimmer
    shimmer = _detune_pad(261.63, duration, n_voices=3, detune_cents=15)
    lfo3 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.02 * t + 2.0)
    shimmer *= lfo3

    # Mix
    mixed = 0.55 * drone_c3 + 0.30 * drone_g3 + 0.15 * shimmer
    peak = np.max(np.abs(mixed))
    if peak > 0:
        mixed /= peak

    # Apply reverb (heavy, for spaciousness)
    mixed = _simple_reverb(mixed, decay_s=3.0, wet=0.45)

    # Fade in/out for clean looping
    audio = _to_audio_segment(mixed)
    audio = audio.fade_in(4000).fade_out(4000) - 6
    audio.export(str(output_path), format="mp3", bitrate="192k")
    logger.info(f"Background music: {output_path.name} ({len(audio) / 1000:.1f}s)")


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
    generate_outro_bed(audio_dir / "outro.mp3")
    generate_transition_stinger(audio_dir / "transition.mp3")
    generate_background_music(audio_dir / "background.mp3")
    generate_cold_open_leadin(audio_dir / "cold_open_leadin.mp3")

    print(f"All assets saved to {audio_dir}/")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_all_assets()
