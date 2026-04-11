"""Backtester agent: run a strategy against a real + synthetic market set.

This is pure compute. No LLM calls, no network, no randomness. The Backtester
is the most-tested module in the codebase because every user-visible metric
eventually flows through it.

Strategy code is executed inside a multiprocessing subprocess via ``safe_exec``
to isolate runaway or malicious code. See ``docs/SECURITY.md`` for the threat
model and the defense rationale.
"""

from __future__ import annotations

import multiprocessing
import pickle
import traceback
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from backend.agents import stats
from backend.config import settings
from backend.exceptions import StrategyExecutionError, StrategyTimeout
from backend.models import (
    BacktestMetrics,
    BacktestResult,
    PercentileBands,
    SyntheticDistribution,
)

if TYPE_CHECKING:
    from backend.agents.market_imaginer import MarketSet


_GHOST_LINE_COUNT = 20


def _simulate_portfolio(
    price_data: pd.DataFrame,
    signals: pd.Series,
) -> list[float]:
    """Run a simple long-only portfolio simulation and return the equity curve.

    The portfolio holds one unit of cash or one unit of the asset at a time.
    Entry on signal == 1, exit on signal == -1. Zero friction. Equity is
    normalized to start at 1.0.
    """
    closes = price_data["close"].to_numpy(dtype=np.float64)
    n = len(closes)
    if n == 0:
        return [1.0]

    sig_arr = signals.to_numpy(dtype=np.float64)
    if len(sig_arr) != n:
        msg = f"Strategy returned {len(sig_arr)} signals for {n} bars"
        raise StrategyExecutionError(msg)

    equity = np.ones(n, dtype=np.float64)
    position = 0

    for i in range(1, n):
        # Mark to market: if we were in a position at the start of bar i,
        # apply the bar's price move to equity.
        if position == 1:
            equity[i] = equity[i - 1] * (closes[i] / closes[i - 1])
        else:
            equity[i] = equity[i - 1]
        # Update position based on the signal from the previous bar
        # (no look-ahead: signal at i-1 is acted on at i).
        prev_signal = sig_arr[i - 1]
        if position == 0 and prev_signal == 1:
            position = 1
        elif position == 1 and prev_signal == -1:
            position = 0

    return equity.tolist()


def _run_strategy_in_subprocess(
    code: str,
    df_pickle: bytes,
    out_queue: multiprocessing.Queue,  # type: ignore[type-arg]
) -> None:
    """Subprocess target: parse code, run ``strategy(df)``, ship result via queue.

    Runs in a fresh Python interpreter (via the ``spawn`` start method) with a
    minimal globals dict. Any exception is pickled and shipped back so the
    parent can re-raise with the original traceback string.
    """
    try:
        df = pickle.loads(df_pickle)  # noqa: S301 — trusted pickle from parent process
        safe_globals: dict[str, object] = {
            "__builtins__": {
                "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
                "enumerate": enumerate, "filter": filter, "float": float, "int": int,
                "isinstance": isinstance, "iter": iter, "len": len, "list": list,
                "map": map, "max": max, "min": min, "range": range, "reversed": reversed,
                "round": round, "set": set, "sorted": sorted, "str": str, "sum": sum,
                "tuple": tuple, "type": type, "zip": zip, "True": True, "False": False,
                "None": None, "print": lambda *a, **k: None,
                "__import__": __import__,
            },
            "pd": pd,
            "np": np,
        }
        exec(code, safe_globals)  # noqa: S102 — sandboxed via subprocess + restricted builtins
        strategy_fn = safe_globals.get("strategy")
        if not callable(strategy_fn):
            out_queue.put(("error", "StrategyExecutionError", "strategy() function not found in code"))
            return
        result = strategy_fn(df.copy())
        if not isinstance(result, pd.Series):
            out_queue.put(("error", "StrategyExecutionError", f"strategy() returned {type(result).__name__}, expected pd.Series"))
            return
        out_queue.put(("ok", pickle.dumps(result)))
    except Exception as exc:  # noqa: BLE001 — intentional: ship all errors to parent
        out_queue.put(("error", type(exc).__name__, f"{exc}\n{traceback.format_exc()}"))


def safe_exec(code: str, df: pd.DataFrame, *, timeout: float | None = None) -> pd.Series:
    """Execute user strategy code in an isolated subprocess with a wall-clock timeout.

    Args:
        code: Validated Python source defining ``def strategy(df)``.
        df: Input OHLCV DataFrame. A copy is sent to the subprocess.
        timeout: Max wall-clock seconds. Defaults to settings.quantforge_exec_timeout.

    Returns:
        The ``pd.Series`` of signals returned by the strategy.

    Raises:
        StrategyTimeout: Subprocess exceeded the timeout.
        StrategyExecutionError: Strategy raised or returned the wrong type.
    """
    limit = timeout if timeout is not None else settings.quantforge_exec_timeout
    ctx = multiprocessing.get_context("spawn")
    q: multiprocessing.Queue = ctx.Queue()  # type: ignore[type-arg]
    proc = ctx.Process(
        target=_run_strategy_in_subprocess,
        args=(code, pickle.dumps(df), q),
    )
    proc.start()
    proc.join(limit)

    if proc.is_alive():
        proc.terminate()
        proc.join(1.0)
        msg = f"Strategy exceeded {limit}s timeout"
        raise StrategyTimeout(msg)

    try:
        payload = q.get_nowait()
    except Exception as exc:  # noqa: BLE001
        msg = "Strategy subprocess produced no result"
        raise StrategyExecutionError(msg) from exc

    tag = payload[0]
    if tag == "ok":
        return pickle.loads(payload[1])  # type: ignore[no-any-return]  # noqa: S301
    _, exc_type, exc_msg = payload
    msg = f"{exc_type}: {exc_msg}"
    raise StrategyExecutionError(msg)


def _metrics_from_curve(curve: list[float]) -> BacktestMetrics:
    """Derive ``BacktestMetrics`` from a single equity curve."""
    return BacktestMetrics(
        total_return=stats.total_return(curve),
        max_drawdown=stats.max_drawdown(curve),
        sharpe=stats.sharpe_ratio(curve),
        equity_curve=curve,
    )


def backtest(code: str, markets: MarketSet, *, timeout: float | None = None) -> BacktestResult:
    """Run the strategy against the real reference and every synthetic scenario.

    Args:
        code: Validated strategy source from the Strategy Architect.
        markets: A ``MarketSet`` from the Market Imaginer.
        timeout: Per-subprocess wall-clock budget; defaults to settings.

    Returns:
        A ``BacktestResult`` populated with real metrics, synthetic
        distributions, percentile bands, and the overfitting percentile.
    """
    real_signals = safe_exec(code, markets.real, timeout=timeout)
    real_curve = _simulate_portfolio(markets.real, real_signals)
    real_metrics = _metrics_from_curve(real_curve)

    synthetic_curves: list[list[float]] = []
    total_returns: list[float] = []
    max_drawdowns: list[float] = []
    sharpes: list[float] = []

    for scenario in markets.scenarios:
        sig = safe_exec(code, scenario, timeout=timeout)
        curve = _simulate_portfolio(scenario, sig)
        synthetic_curves.append(curve)
        total_returns.append(stats.total_return(curve))
        max_drawdowns.append(stats.max_drawdown(curve))
        sharpes.append(stats.sharpe_ratio(curve))

    p05, p50, p95 = stats.percentile_bands(synthetic_curves)
    timestamps = [ts.isoformat() for ts in markets.real.index]

    step = max(1, len(synthetic_curves) // _GHOST_LINE_COUNT)
    ghost_lines = synthetic_curves[::step][:_GHOST_LINE_COUNT]

    synthetic = SyntheticDistribution(
        total_return_distribution=total_returns,
        max_drawdown_distribution=max_drawdowns,
        sharpe_distribution=[s if not np.isnan(s) else 0.0 for s in sharpes],
        percentile_bands=PercentileBands(timestamps=timestamps, p05=p05, p50=p50, p95=p95),
        ghost_lines=ghost_lines,
    )

    return BacktestResult(
        real=real_metrics,
        synthetic=synthetic,
        probability_of_ruin=stats.probability_of_ruin(max_drawdowns),
        overfitting_percentile=stats.overfitting_percentile(real_metrics.total_return, total_returns),
    )
