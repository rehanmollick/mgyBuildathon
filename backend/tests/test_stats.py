"""Tests for backend.agents.stats — pinned against SciPy where possible."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats as scipy_stats

from backend.agents import stats


def test_total_return_simple() -> None:
    assert stats.total_return([1.0, 1.1, 1.21]) == pytest.approx(0.21)


def test_total_return_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        stats.total_return([])


def test_max_drawdown_monotonic_is_zero() -> None:
    assert stats.max_drawdown([1.0, 1.1, 1.2, 1.3]) == pytest.approx(0.0)


def test_max_drawdown_known_case() -> None:
    curve = [1.0, 1.5, 0.75, 1.0]
    # Peak 1.5 → trough 0.75 = -0.5
    assert stats.max_drawdown(curve) == pytest.approx(-0.5)


def test_max_drawdown_empty_raises() -> None:
    with pytest.raises(ValueError):
        stats.max_drawdown([])


def test_sharpe_zero_vol_is_nan() -> None:
    assert math.isnan(stats.sharpe_ratio([1.0, 1.0, 1.0, 1.0]))


def test_sharpe_short_curve_is_nan() -> None:
    assert math.isnan(stats.sharpe_ratio([1.0]))


def test_sharpe_matches_formula() -> None:
    curve = [1.0, 1.01, 1.015, 1.02, 1.03, 1.025, 1.04]
    result = stats.sharpe_ratio(curve)
    assert not math.isnan(result)
    # Hand-compute expected
    arr = np.asarray(curve, dtype=np.float64)
    rets = np.diff(arr) / arr[:-1]
    expected = float(np.mean(rets)) / float(np.std(rets, ddof=1)) * math.sqrt(252)
    assert result == pytest.approx(expected, rel=1e-10)


def test_probability_of_ruin_fraction() -> None:
    dd = [-0.2, -0.6, -0.7, -0.1, -0.51]
    # threshold default = -0.5; items < -0.5 are -0.6, -0.7, -0.51 → 3/5
    assert stats.probability_of_ruin(dd) == pytest.approx(0.6)


def test_probability_of_ruin_empty_is_zero() -> None:
    assert stats.probability_of_ruin([]) == 0.0


def test_overfitting_percentile_matches_scipy() -> None:
    synth = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
    real = 0.22
    ours = stats.overfitting_percentile(real, synth)
    expected = float(scipy_stats.percentileofscore(synth, real, kind="mean"))
    assert ours == pytest.approx(expected, rel=1e-10)


def test_overfitting_percentile_empty_is_fifty() -> None:
    assert stats.overfitting_percentile(0.1, []) == 50.0


def test_percentile_bands_shapes() -> None:
    curves = [[1.0, 1.1, 1.2, 1.3] for _ in range(10)]
    curves.append([1.0, 0.9, 0.8, 0.7])
    p05, p50, p95 = stats.percentile_bands(curves)
    assert len(p05) == 4
    assert len(p50) == 4
    assert len(p95) == 4
    for i in range(4):
        assert p05[i] <= p50[i] <= p95[i]


def test_percentile_bands_empty_returns_empty() -> None:
    p05, p50, p95 = stats.percentile_bands([])
    assert p05 == [] and p50 == [] and p95 == []
