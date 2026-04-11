"""Market Imaginer (GBM): synthetic OHLCV generator for v1.

Uses Geometric Brownian Motion calibrated against the asset's historical
volatility to generate N synthetic market histories. Fast, deterministic under
a seed, and sufficient for the overfitting percentile's ranking behavior (see
``docs/adr/002-gbm-as-primary-generator.md`` for the rationale).

The GBM model simulates log-returns as IID Gaussian with drift mu and
volatility sigma. Close prices are the cumulative product; open, high, and
low are derived from close with per-bar noise that preserves the OHLC
invariants (high >= all, low <= all).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

_TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class MarketSet:
    """A bundle of synthetic market histories plus a real-history reference."""

    asset: str
    real: pd.DataFrame
    scenarios: list[pd.DataFrame]


def _calibrate_from_real(real: pd.DataFrame) -> tuple[float, float]:
    """Return (mu, sigma) from real close-to-close log returns."""
    close = real["close"].to_numpy(dtype=np.float64)
    log_returns = np.diff(np.log(close))
    mu = float(np.mean(log_returns))
    sigma = float(np.std(log_returns, ddof=1)) if len(log_returns) > 1 else 0.01
    if sigma <= 0.0 or np.isnan(sigma):
        sigma = 0.01
    return mu, sigma


def _generate_single(
    *,
    start_price: float,
    n_steps: int,
    mu: float,
    sigma: float,
    rng: np.random.Generator,
    timestamps: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Generate one synthetic OHLCV DataFrame."""
    shocks = rng.standard_normal(n_steps - 1)
    log_rets = mu + sigma * shocks
    log_prices = np.concatenate([[np.log(start_price)], np.log(start_price) + np.cumsum(log_rets)])
    close = np.exp(log_prices)

    intrabar_sigma = sigma * 0.5
    open_noise = rng.standard_normal(n_steps) * intrabar_sigma
    open_ = close * np.exp(open_noise - intrabar_sigma * intrabar_sigma / 2)
    open_[0] = start_price

    high_extra = np.abs(rng.standard_normal(n_steps)) * intrabar_sigma
    low_extra = np.abs(rng.standard_normal(n_steps)) * intrabar_sigma
    high = np.maximum(open_, close) * np.exp(high_extra)
    low = np.minimum(open_, close) * np.exp(-low_extra)

    volume = rng.integers(low=500_000, high=5_000_000, size=n_steps).astype(np.float64)

    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=timestamps,
    )


def _synthetic_real(asset: str, n_steps: int, seed: int) -> pd.DataFrame:
    """Deterministic synthetic "real" DataFrame used when no live data feed is wired.

    v1 does not hit yfinance at request time; it generates a reproducible
    reference path seeded by the asset name so every request against the same
    asset gets the same "real" history. This keeps the pipeline hermetic and
    CI-friendly.
    """
    rng = np.random.default_rng(abs(hash(asset)) % (2**32) ^ seed)
    mu = 0.0004
    sigma = 0.012
    timestamps = pd.bdate_range("2023-07-01", periods=n_steps)
    return _generate_single(
        start_price=420.0,
        n_steps=n_steps,
        mu=mu,
        sigma=sigma,
        rng=rng,
        timestamps=timestamps,
    )


def imagine(
    asset: str,
    n_scenarios: int,
    *,
    n_steps: int = 252,
    seed: int | None = None,
) -> MarketSet:
    """Generate a set of synthetic OHLCV DataFrames plus a reference real DataFrame.

    Args:
        asset: Ticker symbol, used to seed a deterministic "real" reference.
        n_scenarios: Number of synthetic trajectories to generate.
        n_steps: Length of each trajectory in bars (default 252 = 1 trading year).
        seed: Optional seed for reproducibility. When ``None`` a fresh RNG is
            constructed per call, which is what production uses.

    Returns:
        A ``MarketSet`` with the real reference and all synthetic scenarios.
    """
    base_seed = seed if seed is not None else int(np.random.SeedSequence().entropy or 0)
    real = _synthetic_real(asset, n_steps, base_seed)
    mu, sigma = _calibrate_from_real(real)
    start_price = float(real["close"].iloc[0])
    timestamps = pd.DatetimeIndex(real.index)

    scenarios: list[pd.DataFrame] = []
    for i in range(n_scenarios):
        rng = np.random.default_rng(base_seed + i + 1)
        scenarios.append(
            _generate_single(
                start_price=start_price,
                n_steps=n_steps,
                mu=mu,
                sigma=sigma,
                rng=rng,
                timestamps=timestamps,
            )
        )

    return MarketSet(asset=asset, real=real, scenarios=scenarios)
