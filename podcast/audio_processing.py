"""Voice post-processing pipeline for broadcast-quality podcast audio.

Applies high-pass filtering, normalization, dynamic range compression,
and low-pass filtering to each TTS segment before assembly.
"""

from __future__ import annotations

import logging

from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

logger = logging.getLogger(__name__)


def process_voice_segment(audio: AudioSegment) -> AudioSegment:
    """Process a single TTS voice segment for broadcast quality.

    Pipeline:
        1. High-pass filter at 80Hz — remove low rumble and plosive artifacts
        2. Normalize — bring each segment to consistent peak level
        3. Compress dynamic range — tame peaks for even loudness
        4. Low-pass filter at 14kHz — remove high-frequency TTS artifacts
    """
    # 1. Remove low-frequency rumble
    audio = audio.high_pass_filter(80)

    # 2. Normalize to consistent peak level
    audio = normalize(audio, headroom=0.5)

    # 3. Compress for broadcast consistency
    audio = compress_dynamic_range(
        audio,
        threshold=-20.0,
        ratio=3.0,
        attack=5.0,
        release=50.0,
    )

    # 4. Roll off high-frequency TTS artifacts
    audio = audio.low_pass_filter(14000)

    return audio
