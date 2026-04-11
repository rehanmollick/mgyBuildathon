"""Tests for the Backtester agent."""

from __future__ import annotations

import pandas as pd
import pytest

from backend.agents.backtester import _simulate_portfolio, backtest, safe_exec
from backend.agents.market_imaginer import imagine
from backend.exceptions import StrategyExecutionError, StrategyTimeout


def test_safe_exec_happy_path(ohlcv_df: pd.DataFrame, simple_strategy_code: str) -> None:
    signals = safe_exec(simple_strategy_code, ohlcv_df)
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(ohlcv_df)


def test_safe_exec_timeout_raises(ohlcv_df: pd.DataFrame, runaway_strategy_code: str) -> None:
    with pytest.raises(StrategyTimeout):
        safe_exec(runaway_strategy_code, ohlcv_df, timeout=1.0)


def test_safe_exec_exception_raises_execution_error(ohlcv_df: pd.DataFrame) -> None:
    bad_code = (
        "import pandas as pd\n"
        "def strategy(df):\n"
        "    raise ValueError('boom')\n"
    )
    with pytest.raises(StrategyExecutionError, match="boom"):
        safe_exec(bad_code, ohlcv_df)


def test_safe_exec_wrong_return_type_raises(ohlcv_df: pd.DataFrame) -> None:
    bad_code = (
        "import pandas as pd\n"
        "def strategy(df):\n"
        "    return 42\n"
    )
    with pytest.raises(StrategyExecutionError):
        safe_exec(bad_code, ohlcv_df)


def test_simulate_buy_and_hold_matches_close_ratio(ohlcv_df: pd.DataFrame) -> None:
    # Always-long from bar 0: equity at end should equal close[n-1]/close[0].
    import pandas as pd
    signals = pd.Series(1, index=ohlcv_df.index)
    equity = _simulate_portfolio(ohlcv_df, signals)
    expected = ohlcv_df["close"].iloc[-1] / ohlcv_df["close"].iloc[1]
    # Position enters on signal[i-1] at close[i], so we expect close[-1]/close[1]
    assert equity[-1] == pytest.approx(expected, rel=1e-10)


def test_simulate_never_signals_stays_flat(ohlcv_df: pd.DataFrame, no_signal_strategy_code: str) -> None:
    signals = safe_exec(no_signal_strategy_code, ohlcv_df)
    equity = _simulate_portfolio(ohlcv_df, signals)
    assert equity[0] == 1.0
    assert equity[-1] == 1.0


def test_backtest_full_pipeline(simple_strategy_code: str) -> None:
    markets = imagine("SPY", n_scenarios=3, n_steps=40, seed=11)
    result = backtest(simple_strategy_code, markets)
    assert len(result.synthetic.total_return_distribution) == 3
    assert len(result.synthetic.max_drawdown_distribution) == 3
    assert len(result.synthetic.percentile_bands.p05) == 40
    assert len(result.synthetic.percentile_bands.p50) == 40
    assert 0.0 <= result.probability_of_ruin <= 1.0
    assert 0.0 <= result.overfitting_percentile <= 100.0


def test_backtest_ghost_lines_bounded(simple_strategy_code: str) -> None:
    markets = imagine("SPY", n_scenarios=50, n_steps=30, seed=12)
    result = backtest(simple_strategy_code, markets)
    assert len(result.synthetic.ghost_lines) <= 20
    for gl in result.synthetic.ghost_lines:
        assert len(gl) == 30
