"""Golden round-trip tests for every pydantic model in the API contract."""

from __future__ import annotations

import pytest

from backend.models import (
    BacktestMetrics,
    BacktestResult,
    ErrorDetail,
    ErrorResponse,
    EvolveRequest,
    EvolveResult,
    ForgeRequest,
    ForgeResult,
    HealthResponse,
    NarrateRequest,
    NarrateResponse,
    PercentileBands,
    SyntheticDistribution,
    VariantResult,
)


def _sample_backtest_result() -> BacktestResult:
    return BacktestResult(
        real=BacktestMetrics(
            total_return=0.4,
            max_drawdown=-0.12,
            sharpe=1.8,
            equity_curve=[1.0, 1.1, 1.2, 1.4],
        ),
        synthetic=SyntheticDistribution(
            total_return_distribution=[0.02, -0.11, 0.34],
            max_drawdown_distribution=[-0.15, -0.22, -0.08],
            sharpe_distribution=[0.3, 1.1, 0.9],
            percentile_bands=PercentileBands(
                timestamps=["2023-07-01", "2023-07-02", "2023-07-03", "2023-07-04"],
                p05=[1.0, 0.97, 0.95, 0.90],
                p50=[1.0, 1.01, 1.02, 1.05],
                p95=[1.0, 1.05, 1.10, 1.20],
            ),
            ghost_lines=[[1.0, 1.02, 1.03, 1.05]],
        ),
        probability_of_ruin=0.18,
        overfitting_percentile=94.3,
    )


def test_forge_request_round_trip() -> None:
    r = ForgeRequest(description="Buy when RSI drops below 30", asset="SPY", n_scenarios=200)
    parsed = ForgeRequest.model_validate_json(r.model_dump_json())
    assert parsed == r


def test_forge_request_rejects_short_description() -> None:
    with pytest.raises(Exception):
        ForgeRequest(description="short")


def test_forge_request_rejects_invalid_asset() -> None:
    with pytest.raises(Exception):
        ForgeRequest(description="Buy and hold SPY as baseline", asset="spy12345")


def test_forge_request_normalizes_asset_case() -> None:
    r = ForgeRequest(description="Buy and hold SPY as baseline", asset="spy")
    assert r.asset == "SPY"


def test_forge_result_round_trip() -> None:
    r = ForgeResult(
        request_id="req_abc123def456",
        code="def strategy(df): pass",
        summary="Solid.",
        result=_sample_backtest_result(),
        verdict="Multi-sentence verdict.",
    )
    parsed = ForgeResult.model_validate_json(r.model_dump_json())
    assert parsed == r


def test_evolve_request_round_trip() -> None:
    r = EvolveRequest(description="RSI strategy with filter", n_variants=10)
    parsed = EvolveRequest.model_validate_json(r.model_dump_json())
    assert parsed == r


def test_evolve_result_round_trip() -> None:
    base = VariantResult(
        rank=1,
        description="baseline",
        code="def strategy(df): pass",
        result=_sample_backtest_result(),
        overfitting_percentile=50.0,
    )
    r = EvolveResult(request_id="req_1", baseline=base, variants=[base], verdict="...")
    parsed = EvolveResult.model_validate_json(r.model_dump_json())
    assert parsed == r


def test_narrate_request_round_trip() -> None:
    r = NarrateRequest(verdict_text="Your strategy looks robust.")
    parsed = NarrateRequest.model_validate_json(r.model_dump_json())
    assert parsed == r


def test_narrate_response_round_trip() -> None:
    r = NarrateResponse(
        request_id="req_x",
        audio_url="/static/audio/verdict_abc.wav",
        duration_seconds=8.4,
        source="stub",
    )
    parsed = NarrateResponse.model_validate_json(r.model_dump_json())
    assert parsed == r


def test_health_response_round_trip() -> None:
    r = HealthResponse(
        status="ok",
        version="0.1.0",
        generator="gbm",
        anthropic_available=True,
        kronos_available=False,
        uptime_seconds=123,
    )
    parsed = HealthResponse.model_validate_json(r.model_dump_json())
    assert parsed == r


def test_error_response_round_trip() -> None:
    r = ErrorResponse(
        error=ErrorDetail(
            code="STRATEGY_TIMEOUT",
            message="Strategy exceeded 5s",
            details={"timeout": 5.0},
            request_id="req_e",
        )
    )
    parsed = ErrorResponse.model_validate_json(r.model_dump_json())
    assert parsed == r
