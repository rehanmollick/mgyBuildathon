"""Tests for the Narrator stub."""

from __future__ import annotations

from backend.agents.narrator import narrate


def test_returns_stable_url_for_same_text() -> None:
    a = narrate("Hello world.")
    b = narrate("Hello world.")
    assert a.audio_url == b.audio_url


def test_different_text_different_url() -> None:
    a = narrate("One.")
    b = narrate("Two.")
    assert a.audio_url != b.audio_url


def test_source_is_stub() -> None:
    a = narrate("hi")
    assert a.source == "stub"


def test_duration_is_positive() -> None:
    a = narrate("a b c d e f g")
    assert a.duration_seconds > 0
