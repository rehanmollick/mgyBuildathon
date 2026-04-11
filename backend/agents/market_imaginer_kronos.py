"""Market Imaginer (Kronos): foundation-model alternate generator for v2.

Exposes the same ``imagine()`` function signature as
``backend.agents.market_imaginer`` so the orchestrator can swap
implementations via a config flag. In v1 this module is shipped as code but
not exercised in CI; calling it without Kronos weights raises
``ModelUnavailable``.

See ``docs/adr/002-gbm-as-primary-generator.md`` for the v1/v2 split rationale.
"""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

from backend.exceptions import ModelUnavailable

if TYPE_CHECKING:
    from backend.agents.market_imaginer import MarketSet


def _kronos_available() -> bool:
    """Return True if the Kronos package can be imported."""
    return importlib.util.find_spec("kronos") is not None


def imagine(
    asset: str,
    n_scenarios: int,
    *,
    n_steps: int = 252,
    seed: int | None = None,
) -> MarketSet:
    """Generate synthetic markets using the Kronos foundation model.

    In v1 this raises ``ModelUnavailable`` unconditionally because the Kronos
    weights are not shipped with the repository. v2 wires the real inference
    path. The function signature matches ``market_imaginer.imagine`` exactly
    so selection happens at import time (see ``backend/orchestrator.py``).

    Raises:
        ModelUnavailable: Kronos weights not present in v1.
    """
    del asset, n_scenarios, n_steps, seed  # unused until v2
    if not _kronos_available():
        msg = (
            "Kronos generator selected but the 'kronos' package is not installed. "
            "Install weights and retry, or fall back to QUANTFORGE_GENERATOR=gbm."
        )
        raise ModelUnavailable(msg)
    # v2: real Kronos inference wired here.
    msg = "Kronos inference path is a v2 feature and is not wired in v1."
    raise ModelUnavailable(msg)
