"""Tests for the Analyst agent."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.agents.analyst import analyze
from backend.agents.backtester import backtest
from backend.agents.market_imaginer import imagine
from backend.exceptions import ModelUnavailable


def _resp(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[SimpleNamespace(text=text, type="text")])


def _mock(text: str) -> MagicMock:
    m = MagicMock()
    m.messages.create.return_value = _resp(text)
    return m


def _sample_result(simple_strategy_code: str):  # type: ignore[no-untyped-def]
    markets = imagine("SPY", n_scenarios=3, n_steps=30, seed=5)
    return backtest(simple_strategy_code, markets)


def test_happy_path(simple_strategy_code: str) -> None:
    result = _sample_result(simple_strategy_code)
    client = _mock(
        '{"summary": "Looks robust.", "verdict": "Your strategy performed near the median of synthetic runs."}'
    )
    v = analyze(result, client=client)
    assert v.summary == "Looks robust."
    assert "synthetic" in v.verdict


def test_malformed_json_uses_fallback(simple_strategy_code: str) -> None:
    result = _sample_result(simple_strategy_code)
    client = _mock("not valid json at all")
    v = analyze(result, client=client)
    assert v.summary  # fallback summary is non-empty
    assert v.verdict


def test_network_failure_raises_model_unavailable(simple_strategy_code: str) -> None:
    result = _sample_result(simple_strategy_code)
    client = MagicMock()
    client.messages.create.side_effect = RuntimeError("no route to host")
    with pytest.raises(ModelUnavailable):
        analyze(result, client=client)


def test_fenced_json_still_parses(simple_strategy_code: str) -> None:
    result = _sample_result(simple_strategy_code)
    client = _mock('```json\n{"summary": "X", "verdict": "Y"}\n```')
    v = analyze(result, client=client)
    assert v.summary == "X"
    assert v.verdict == "Y"
