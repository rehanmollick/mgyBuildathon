"""Orchestrator: composes the six agents into the Forge and Evolve pipelines.

This file is intentionally short. It imports each agent's top-level function,
calls them in order, and assembles the response model. No classes, no
registries, no dispatch tables. See ``docs/adr/001-multi-agent-architecture.md``
for the rationale.
"""

from __future__ import annotations

import secrets
from typing import Any

from backend.agents import backtester, mutator, narrator
from backend.agents.analyst import analyze
from backend.agents.strategy_architect import architect
from backend.config import settings
from backend.logging_setup import get_logger
from backend.models import (
    EvolveRequest,
    EvolveResult,
    ForgeRequest,
    ForgeResult,
    NarrateRequest,
    NarrateResponse,
    VariantResult,
)

log = get_logger(__name__)


def _new_request_id() -> str:
    """Return a fresh opaque request id."""
    return f"req_{secrets.token_hex(6)}"


def _select_imaginer() -> Any:
    """Import-time switch between the GBM and Kronos generators."""
    if settings.quantforge_generator == "kronos":
        from backend.agents.market_imaginer_kronos import imagine as _imagine
    else:
        from backend.agents.market_imaginer import imagine as _imagine
    return _imagine


def forge(request: ForgeRequest, *, client: Any) -> ForgeResult:
    """Run the full Forge pipeline: architect → imagine → backtest → analyze.

    Args:
        request: Validated ``ForgeRequest``.
        client: An ``anthropic.Anthropic`` instance (or mock).

    Returns:
        A fully-populated ``ForgeResult``.
    """
    request_id = _new_request_id()
    log.info("forge.start", request_id=request_id, asset=request.asset, n=request.n_scenarios)

    strategy = architect(request.description, client=client)
    imagine_fn = _select_imaginer()
    markets = imagine_fn(request.asset, request.n_scenarios, seed=request.seed)
    result = backtester.backtest(strategy.source, markets)
    verdict = analyze(result, client=client)

    log.info(
        "forge.end",
        request_id=request_id,
        overfitting_percentile=result.overfitting_percentile,
    )
    return ForgeResult(
        request_id=request_id,
        code=strategy.source,
        summary=verdict.summary,
        result=result,
        verdict=verdict.verdict,
    )


def evolve(request: EvolveRequest, *, client: Any) -> EvolveResult:
    """Run the Evolve pipeline: baseline → N variants → rank by overfitting.

    The Mutator produces up to ``n_variants`` candidate strategies. Each
    candidate is backtested against the same synthetic market set as the
    baseline, so the ranking is apples-to-apples. Variants are sorted by
    proximity to the 50th overfitting percentile (most robust first).

    Args:
        request: Validated ``EvolveRequest``.
        client: An ``anthropic.Anthropic`` instance (or mock).

    Returns:
        A fully-populated ``EvolveResult``.
    """
    request_id = _new_request_id()
    log.info("evolve.start", request_id=request_id, n_variants=request.n_variants)

    baseline_strategy = architect(request.description, client=client)
    imagine_fn = _select_imaginer()
    markets = imagine_fn(request.asset, request.n_scenarios, seed=request.seed)

    baseline_result = backtester.backtest(baseline_strategy.source, markets)
    baseline_verdict = analyze(baseline_result, client=client)
    baseline_variant = VariantResult(
        rank=0 + 1,  # placeholder; ranked after sort
        description=request.description,
        code=baseline_strategy.source,
        result=baseline_result,
        overfitting_percentile=baseline_result.overfitting_percentile,
    )

    raw_variants = mutator.mutate(request.description, request.n_variants, client=client)
    scored: list[VariantResult] = []
    for variant in raw_variants:
        try:
            r = backtester.backtest(variant.code.source, markets)
        except Exception as exc:  # noqa: BLE001
            log.warning("evolve.variant_failed", error=str(exc))
            continue
        scored.append(
            VariantResult(
                rank=1,  # re-ranked below
                description=variant.description,
                code=variant.code.source,
                result=r,
                overfitting_percentile=r.overfitting_percentile,
            )
        )

    # Sort by distance from 50 (most robust first), then assign ranks.
    scored.sort(key=lambda v: abs(v.overfitting_percentile - 50.0))
    ranked: list[VariantResult] = [
        VariantResult(
            rank=i + 1,
            description=v.description,
            code=v.code,
            result=v.result,
            overfitting_percentile=v.overfitting_percentile,
        )
        for i, v in enumerate(scored)
    ]

    log.info("evolve.end", request_id=request_id, variants_kept=len(ranked))
    return EvolveResult(
        request_id=request_id,
        baseline=baseline_variant,
        variants=ranked,
        verdict=baseline_verdict.verdict,
    )


def narrate(request: NarrateRequest) -> NarrateResponse:
    """Run the Narrator pipeline (stubbed in v1)."""
    request_id = _new_request_id()
    ref = narrator.narrate(request.verdict_text)
    return NarrateResponse(
        request_id=request_id,
        audio_url=ref.audio_url,
        duration_seconds=ref.duration_seconds,
        source=ref.source,
    )
