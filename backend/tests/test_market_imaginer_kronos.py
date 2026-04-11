"""Tests for the Kronos Market Imaginer stub."""

from __future__ import annotations

import pytest

from backend.agents.market_imaginer_kronos import imagine
from backend.exceptions import ModelUnavailable


def test_v1_raises_model_unavailable() -> None:
    with pytest.raises(ModelUnavailable):
        imagine("SPY", n_scenarios=5, n_steps=20, seed=1)


def test_error_message_is_helpful() -> None:
    try:
        imagine("SPY", n_scenarios=5)
    except ModelUnavailable as exc:
        assert "Kronos" in exc.message or "kronos" in exc.message
        assert "gbm" in exc.message.lower()
