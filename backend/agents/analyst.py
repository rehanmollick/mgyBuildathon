"""Analyst agent: backtest metrics → narrative verdict.

Takes a ``BacktestResult`` and calls Claude with a structured prompt asking
for a plain-English verdict on the strategy. The Analyst does not see the
strategy source code or the user's original description; it only sees the
metrics. This keeps prompt-injection surface to zero and makes the verdict
deterministic in structure (always framed around the same numeric cues).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any

from backend.config import settings
from backend.exceptions import ModelUnavailable
from backend.models import BacktestResult

_SYSTEM_PROMPT = """You are a senior quantitative analyst writing a plain-English verdict on a
trading strategy's stress test.

You will be given these numbers:
- real_total_return: the strategy's return on the real market
- synthetic_median_return: the median return across N synthetic markets
- synthetic_return_std: standard deviation of synthetic returns
- probability_of_ruin: fraction of synthetic runs that lost more than 50%
- overfitting_percentile: percentile of the real return within the synthetic distribution (0..100)
- max_drawdown_real: worst peak-to-trough on real data
- sharpe_real: annualized Sharpe on real data

Your job:
1. Write a short "summary" (one sentence) for inline display.
2. Write a "verdict" (3-5 sentences) suitable for narration. Explain what the numbers mean in
   language a smart retail trader could follow. Be honest: if the strategy looks overfit
   (percentile > 90), say so. If it looks robust (percentile near 50), say so. Never sugar-coat.

Return a JSON object with exactly two keys: "summary" and "verdict". No other keys, no prose
outside the JSON.
"""


@dataclass(frozen=True)
class Verdict:
    """Analyst output: inline summary + narratable verdict."""

    summary: str
    verdict: str


def _format_prompt(result: BacktestResult) -> str:
    """Flatten a BacktestResult into the numeric cues the Analyst reads."""
    synth = result.synthetic.total_return_distribution
    median = statistics.median(synth) if synth else 0.0
    std = statistics.stdev(synth) if len(synth) > 1 else 0.0
    return (
        f"real_total_return: {result.real.total_return:.4f}\n"
        f"synthetic_median_return: {median:.4f}\n"
        f"synthetic_return_std: {std:.4f}\n"
        f"probability_of_ruin: {result.probability_of_ruin:.4f}\n"
        f"overfitting_percentile: {result.overfitting_percentile:.2f}\n"
        f"max_drawdown_real: {result.real.max_drawdown:.4f}\n"
        f"sharpe_real: {result.real.sharpe:.4f}\n"
    )


def _parse_claude_json(text: str) -> tuple[str, str]:
    """Extract ``summary`` and ``verdict`` from Claude's JSON response."""
    import json

    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[len("json") :].strip()
        if stripped.endswith("```"):
            stripped = stripped[: -len("```")].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        return _fallback_verdict()
    try:
        obj = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return _fallback_verdict()
    summary = str(obj.get("summary") or "").strip()
    verdict = str(obj.get("verdict") or "").strip()
    if not summary or not verdict:
        return _fallback_verdict()
    return summary, verdict


def _fallback_verdict() -> tuple[str, str]:
    """Safe fallback used when Claude's response cannot be parsed."""
    return (
        "Stress test complete.",
        (
            "The stress test finished, but the analyst could not produce a narrative verdict. "
            "Review the dashboard metrics for details."
        ),
    )


def analyze(result: BacktestResult, *, client: Any) -> Verdict:
    """Produce a narrative verdict for a ``BacktestResult``.

    Args:
        result: Populated BacktestResult from the Backtester.
        client: An ``anthropic.Anthropic`` instance (injected for tests).

    Returns:
        A ``Verdict`` with inline summary and narratable text.

    Raises:
        ModelUnavailable: Anthropic API was unreachable.
    """
    prompt = _format_prompt(result)
    try:
        response = client.messages.create(
            model=settings.quantforge_claude_model,
            max_tokens=settings.quantforge_claude_max_tokens,
            temperature=settings.quantforge_claude_temperature,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        msg = f"Anthropic API unreachable for Analyst: {exc}"
        raise ModelUnavailable(msg) from exc

    blocks = getattr(response, "content", []) or []
    parts: list[str] = []
    for block in blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    joined = "".join(parts).strip()
    summary, verdict = _parse_claude_json(joined) if joined else _fallback_verdict()
    return Verdict(summary=summary, verdict=verdict)
