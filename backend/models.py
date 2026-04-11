"""Pydantic v2 models — the source of truth for the QuantForge API contract.

Any change here must be mirrored in ``frontend/src/lib/types.ts`` and pinned
by a round-trip test in ``tests/test_api_contracts.py``. See ``docs/SCHEMA.md``
for the field-by-field rationale.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------- request models ----------


class ForgeRequest(BaseModel):
    """Request body for ``POST /api/forge``."""

    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    description: str = Field(..., min_length=10, max_length=2000)
    asset: str = Field(default="SPY", pattern=r"^[A-Z]{1,6}$")
    n_scenarios: int = Field(default=200, ge=20, le=1000)
    seed: int | None = Field(default=None, ge=0)

    @field_validator("asset", mode="before")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.upper() if isinstance(value, str) else value


class EvolveRequest(BaseModel):
    """Request body for ``POST /api/evolve``."""

    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    description: str = Field(..., min_length=10, max_length=2000)
    asset: str = Field(default="SPY", pattern=r"^[A-Z]{1,6}$")
    n_variants: int = Field(default=10, ge=2, le=20)
    n_scenarios: int = Field(default=200, ge=20, le=1000)
    seed: int | None = Field(default=None, ge=0)

    @field_validator("asset", mode="before")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.upper() if isinstance(value, str) else value


class NarrateRequest(BaseModel):
    """Request body for ``POST /api/narrate``."""

    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    verdict_text: str = Field(..., min_length=1, max_length=1000)


# ---------- metric models ----------


class BacktestMetrics(BaseModel):
    """Metrics for a single backtest run (real or synthetic)."""

    model_config = ConfigDict(frozen=True)

    total_return: float
    max_drawdown: float
    sharpe: float
    equity_curve: list[float]


class PercentileBands(BaseModel):
    """Fan-chart percentile bands for the synthetic distribution."""

    model_config = ConfigDict(frozen=True)

    timestamps: list[str]
    p05: list[float]
    p50: list[float]
    p95: list[float]


class SyntheticDistribution(BaseModel):
    """Distribution of metrics across N synthetic runs."""

    model_config = ConfigDict(frozen=True)

    total_return_distribution: list[float]
    max_drawdown_distribution: list[float]
    sharpe_distribution: list[float]
    percentile_bands: PercentileBands
    ghost_lines: list[list[float]]


class BacktestResult(BaseModel):
    """Full result object produced by the Backtester agent."""

    model_config = ConfigDict(frozen=True)

    real: BacktestMetrics
    synthetic: SyntheticDistribution
    probability_of_ruin: float = Field(..., ge=0.0, le=1.0)
    overfitting_percentile: float = Field(..., ge=0.0, le=100.0)


# ---------- response models ----------


class ForgeResult(BaseModel):
    """Response body for ``POST /api/forge``."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    code: str
    summary: str
    result: BacktestResult
    verdict: str


class VariantResult(BaseModel):
    """A single mutated variant plus its backtest result."""

    model_config = ConfigDict(frozen=True)

    rank: int = Field(..., ge=1)
    description: str
    code: str
    result: BacktestResult
    overfitting_percentile: float = Field(..., ge=0.0, le=100.0)


class EvolveResult(BaseModel):
    """Response body for ``POST /api/evolve``."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    baseline: VariantResult
    variants: list[VariantResult]
    verdict: str


class NarrateResponse(BaseModel):
    """Response body for ``POST /api/narrate``."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    audio_url: str
    duration_seconds: float = Field(..., ge=0.0)
    source: Literal["stub", "vibevoice"]


class HealthResponse(BaseModel):
    """Response body for ``GET /api/health``."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok", "degraded"]
    version: str
    generator: Literal["gbm", "kronos"]
    anthropic_available: bool
    kronos_available: bool
    uptime_seconds: int = Field(..., ge=0)


# ---------- error envelope ----------


class ErrorDetail(BaseModel):
    """Inner error payload for the ``ErrorResponse`` envelope."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)
    request_id: str


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all endpoints on failure."""

    model_config = ConfigDict(frozen=True)

    error: ErrorDetail
