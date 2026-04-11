"""Pure-math helpers shared across agents.

Every function here is a pure function with typed inputs and outputs. No I/O,
no LLM calls, no randomness (unless passed in). These are the routines that
the Backtester and the Analyst lean on for metric computation.

The implementations are deliberately simple: one correct formula per metric.
Where possible we cross-check against SciPy in tests (see
``tests/test_stats.py``) to pin our implementations against ground truth.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from scipy import stats as scipy_stats

_TRADING_DAYS_PER_YEAR = 252
_RUIN_DRAWDOWN_THRESHOLD = -0.5


def sharpe_ratio(
    equity_curve: Sequence[float], *, periods_per_year: int = _TRADING_DAYS_PER_YEAR
) -> float:
    """Annualized Sharpe ratio for an equity curve normalized to start at 1.0.

    Returns NaN for a curve with zero volatility (flat equity).
    """
    if len(equity_curve) < 2:
        return float("nan")
    arr = np.asarray(equity_curve, dtype=np.float64)
    returns = np.diff(arr) / arr[:-1]
    std = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0
    if std == 0.0 or math.isnan(std):
        return float("nan")
    mean = float(np.mean(returns))
    return mean / std * math.sqrt(periods_per_year)


def max_drawdown(equity_curve: Sequence[float]) -> float:
    """Maximum peak-to-trough drawdown as a negative decimal.

    Returns 0.0 for a monotonically non-decreasing curve. An empty curve
    raises ``ValueError``.
    """
    if not equity_curve:
        msg = "max_drawdown: empty equity curve"
        raise ValueError(msg)
    arr = np.asarray(equity_curve, dtype=np.float64)
    running_peak = np.maximum.accumulate(arr)
    drawdown = (arr - running_peak) / running_peak
    return float(np.min(drawdown))


def total_return(equity_curve: Sequence[float]) -> float:
    """Total return of an equity curve normalized to start at 1.0."""
    if not equity_curve:
        msg = "total_return: empty equity curve"
        raise ValueError(msg)
    return float(equity_curve[-1]) / float(equity_curve[0]) - 1.0


def probability_of_ruin(
    drawdowns: Sequence[float],
    *,
    threshold: float = _RUIN_DRAWDOWN_THRESHOLD,
) -> float:
    """Fraction of synthetic runs whose max drawdown was worse than ``threshold``.

    ``threshold`` defaults to -0.5, meaning "lost more than 50%". The caller
    passes in a distribution of drawdowns (one per synthetic scenario).
    """
    if not drawdowns:
        return 0.0
    arr = np.asarray(drawdowns, dtype=np.float64)
    return float(np.mean(arr < threshold))


def overfitting_percentile(real_return: float, synthetic_returns: Sequence[float]) -> float:
    """Percentile-of-score of ``real_return`` against ``synthetic_returns``.

    Uses ``scipy.stats.percentileofscore`` with the "mean" kind, which is the
    distribution-free definition most robust to ties. Returns a value in [0, 100].
    A value near 50 means the real run is typical; values near 95+ suggest the
    strategy overfit to the real market.
    """
    if not synthetic_returns:
        return 50.0
    arr = np.asarray(synthetic_returns, dtype=np.float64)
    return float(scipy_stats.percentileofscore(arr, real_return, kind="mean"))


def percentile_bands(
    curves: Sequence[Sequence[float]],
    *,
    lower: float = 5.0,
    upper: float = 95.0,
) -> tuple[list[float], list[float], list[float]]:
    """Compute per-timestep percentile bands across a collection of equity curves.

    All input curves must have the same length. Returns a tuple
    ``(p_lower, p_median, p_upper)`` of per-timestep percentile values.
    """
    if not curves:
        return [], [], []
    arr = np.asarray(curves, dtype=np.float64)
    if arr.ndim != 2:
        msg = f"percentile_bands: expected 2D array, got shape {arr.shape}"
        raise ValueError(msg)
    p_lo = np.percentile(arr, lower, axis=0)
    p_md = np.percentile(arr, 50.0, axis=0)
    p_hi = np.percentile(arr, upper, axis=0)
    return p_lo.tolist(), p_md.tolist(), p_hi.tolist()
