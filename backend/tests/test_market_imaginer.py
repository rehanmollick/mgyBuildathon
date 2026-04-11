"""Tests for the GBM Market Imaginer."""

from __future__ import annotations

import numpy as np
import pytest

from backend.agents.market_imaginer import imagine


def test_returns_exact_scenario_count() -> None:
    m = imagine("SPY", n_scenarios=10, n_steps=50, seed=1)
    assert len(m.scenarios) == 10


def test_each_scenario_has_correct_length() -> None:
    m = imagine("SPY", n_scenarios=5, n_steps=100, seed=1)
    for df in m.scenarios:
        assert len(df) == 100


def test_columns_are_ohlcv() -> None:
    m = imagine("SPY", n_scenarios=2, n_steps=20, seed=1)
    for df in m.scenarios:
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_ohlc_invariants() -> None:
    m = imagine("SPY", n_scenarios=20, n_steps=50, seed=2)
    for df in m.scenarios:
        assert (df["high"] >= df["close"]).all()
        assert (df["high"] >= df["open"]).all()
        assert (df["high"] >= df["low"]).all()
        assert (df["low"] <= df["close"]).all()
        assert (df["low"] <= df["open"]).all()


def test_all_prices_positive() -> None:
    m = imagine("SPY", n_scenarios=10, n_steps=50, seed=3)
    for df in m.scenarios:
        assert (df[["open", "high", "low", "close"]] > 0).all().all()


def test_deterministic_under_seed() -> None:
    a = imagine("SPY", n_scenarios=3, n_steps=50, seed=42)
    b = imagine("SPY", n_scenarios=3, n_steps=50, seed=42)
    for x, y in zip(a.scenarios, b.scenarios):
        np.testing.assert_array_equal(x["close"].to_numpy(), y["close"].to_numpy())


def test_different_seeds_differ() -> None:
    a = imagine("SPY", n_scenarios=3, n_steps=50, seed=1)
    b = imagine("SPY", n_scenarios=3, n_steps=50, seed=999)
    assert not np.array_equal(a.scenarios[0]["close"].to_numpy(), b.scenarios[0]["close"].to_numpy())


def test_real_reference_shape() -> None:
    m = imagine("SPY", n_scenarios=2, n_steps=30, seed=1)
    assert len(m.real) == 30
    assert list(m.real.columns) == ["open", "high", "low", "close", "volume"]


def test_asset_label_preserved() -> None:
    m = imagine("QQQ", n_scenarios=1, n_steps=10, seed=1)
    assert m.asset == "QQQ"
