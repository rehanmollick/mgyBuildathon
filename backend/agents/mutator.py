"""Strategy Mutator agent: baseline strategy → N plausible variants.

Calls Claude with the baseline description and asks for N mutations as JSON.
Each returned variant is independently validated via the same AST rules as
the Strategy Architect. Invalid variants are dropped silently (with a log)
rather than failing the whole Evolve run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from backend.agents.strategy_architect import StrategyCode, _extract_code_block, _validate_ast
from backend.config import settings
from backend.exceptions import ModelUnavailable, StrategyParseError
from backend.logging_setup import get_logger

log = get_logger(__name__)

_SYSTEM_PROMPT = """You are a quantitative strategy researcher. Given a baseline trading strategy description, generate {n} variations that might be more robust.

For each variation:
1. Change parameters (different MA periods, different thresholds).
2. Add filters (volume confirmation, trend filter).
3. Combine with other indicators.
4. Adjust risk management (stop losses, position sizing).

Return a JSON array of exactly {n} objects. Each object must have:
- "description": plain-English explanation of what changed
- "code": Python source implementing 'def strategy(df: pd.DataFrame) -> pd.Series' using only pandas, numpy, math, and standard Python.

Return ONLY the JSON array. No prose, no fenced block markers.
"""


@dataclass(frozen=True)
class StrategyVariant:
    """One validated variant produced by the Mutator."""

    description: str
    code: StrategyCode


def _parse_variants(text: str, n_requested: int) -> list[tuple[str, str]]:
    """Parse Claude's JSON array into (description, code) pairs.

    Drops anything that does not match the expected shape.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[len("json") :].strip()
        if stripped.endswith("```"):
            stripped = stripped[: -len("```")].strip()
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        arr = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        log.warning("mutator.parse_failed", n_requested=n_requested)
        return []
    if not isinstance(arr, list):
        return []
    result: list[tuple[str, str]] = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        desc = item.get("description")
        code = item.get("code")
        if isinstance(desc, str) and isinstance(code, str) and desc.strip() and code.strip():
            result.append((desc.strip(), code.strip()))
    return result


def mutate(
    baseline_description: str,
    n_variants: int,
    *,
    client: Any,
) -> list[StrategyVariant]:
    """Produce up to ``n_variants`` validated mutations of the baseline.

    Args:
        baseline_description: The user's original strategy description.
        n_variants: Target number of variants.
        client: An ``anthropic.Anthropic`` instance (injected for tests).

    Returns:
        A list of ``StrategyVariant``. May be shorter than ``n_variants``
        if some candidates failed AST validation.

    Raises:
        ModelUnavailable: Anthropic API was unreachable.
    """
    try:
        response = client.messages.create(
            model=settings.quantforge_claude_model,
            max_tokens=settings.quantforge_claude_max_tokens * 2,
            temperature=settings.quantforge_claude_temperature,
            system=_SYSTEM_PROMPT.format(n=n_variants),
            messages=[{"role": "user", "content": baseline_description}],
        )
    except Exception as exc:
        msg = f"Anthropic API unreachable for Mutator: {exc}"
        raise ModelUnavailable(msg) from exc

    blocks = getattr(response, "content", []) or []
    parts: list[str] = []
    for block in blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    joined = "".join(parts)

    candidates = _parse_variants(joined, n_variants)
    variants: list[StrategyVariant] = []
    for desc, raw_code in candidates:
        code = _extract_code_block(raw_code)
        try:
            _validate_ast(code)
        except StrategyParseError as exc:
            log.info("mutator.variant_dropped", reason=exc.message)
            continue
        variants.append(
            StrategyVariant(
                description=desc,
                code=StrategyCode(source=code, description=desc),
            )
        )
    return variants
