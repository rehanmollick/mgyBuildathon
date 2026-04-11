"""Narrator agent: verdict text → audio reference.

v1 ships a deterministic stub that returns a pre-recorded audio URL based on
a hash of the verdict text. This lets the frontend integrate the
``VerdictPlayer`` component and demo the flow without needing the VibeVoice
model shipped. v2 wires the real TTS path.

The function signature is stable across v1 and v2 so the orchestrator does
not need to change when TTS is added.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

NarratorSource = Literal["stub", "vibevoice"]


@dataclass(frozen=True)
class AudioRef:
    """Reference to a synthesized audio clip."""

    audio_url: str
    duration_seconds: float
    source: NarratorSource


def narrate(verdict_text: str) -> AudioRef:
    """Return a stable audio reference for a verdict string.

    In v1 this returns a hashed URL under ``/static/audio/`` with a duration
    estimated from word count at 150 wpm. No file is actually written; the
    frontend's fallback player renders a silent waveform when the URL does
    not resolve. v2 will produce a real WAV file via VibeVoice.
    """
    digest = hashlib.sha1(verdict_text.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
    audio_url = f"/static/audio/verdict_{digest}.wav"
    words = max(1, len(verdict_text.split()))
    duration_seconds = round(words / 2.5, 1)  # ~150 wpm ≈ 2.5 wps
    return AudioRef(audio_url=audio_url, duration_seconds=duration_seconds, source="stub")
