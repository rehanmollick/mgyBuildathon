"""Strategy Architect agent: English description → typed Python strategy code.

Calls Claude with a narrow system prompt, then validates the returned code at
the AST level before returning it. Validation enforces three rules:

1. The code must contain exactly one top-level ``def strategy(df)`` function.
2. The function must have the exact signature ``def strategy(df: pd.DataFrame) -> pd.Series``.
3. Only allow-listed imports are permitted (``pandas``, ``numpy``, ``math``, a few stdlib).

If any rule fails, ``StrategyParseError`` is raised with a detailed message.
The orchestrator catches this and returns a 400 response with the
``STRATEGY_PARSE_ERROR`` code.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from backend.config import settings
from backend.exceptions import ModelUnavailable, StrategyParseError

if TYPE_CHECKING:
    from anthropic import Anthropic

_ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {"pandas", "numpy", "math", "statistics", "typing", "collections", "itertools"}
)

_SYSTEM_PROMPT = """You are a quantitative finance code generator. Convert the user's trading strategy description into a Python function with this exact signature:

def strategy(df: pd.DataFrame) -> pd.Series:
    \"\"\"Args:
        df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume'].
        Index is DatetimeIndex.
    Returns:
        pd.Series of signals: 1 = buy, -1 = sell, 0 = hold. Same length as df.
    \"\"\"

Rules:
- Use only pandas, numpy, math, and standard Python. No external trading libraries.
- Implement all indicators from scratch (moving averages, RSI, MACD, Bollinger Bands).
- The function must be deterministic for a given input DataFrame.
- Return ONLY the Python code inside a ```python fenced block. No prose, no explanation.
- Imports must be at the top of the code block, before the function definition.
"""


@dataclass(frozen=True)
class StrategyCode:
    """Validated, parseable strategy source code ready for safe execution."""

    source: str
    description: str


def _extract_code_block(text: str) -> str:
    """Pull the Python code out of a Claude response, handling fenced blocks."""
    stripped = text.strip()
    if "```python" in stripped:
        start = stripped.index("```python") + len("```python")
        rest = stripped[start:]
        end = rest.find("```")
        if end == -1:
            return rest.strip()
        return rest[:end].strip()
    if stripped.startswith("```"):
        inner = stripped.strip("`").strip()
        if inner.startswith("python"):
            inner = inner[len("python") :].strip()
        return inner
    return stripped


def _validate_ast(source: str) -> None:
    """Reject code that breaks the contract or imports forbidden modules."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        msg = f"Generated code is not valid Python: {exc.msg}"
        raise StrategyParseError(msg, details={"line": exc.lineno, "offset": exc.offset}) from exc

    strategy_defs: list[ast.FunctionDef] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in _ALLOWED_IMPORTS:
                    msg = f"Import not allowed: {alias.name}"
                    raise StrategyParseError(msg, details={"module": alias.name})
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root and root not in _ALLOWED_IMPORTS:
                msg = f"Import not allowed: from {node.module}"
                raise StrategyParseError(msg, details={"module": node.module})
        elif isinstance(node, ast.FunctionDef) and node.name == "strategy":
            strategy_defs.append(node)

    if len(strategy_defs) != 1:
        msg = f"Expected exactly one top-level 'strategy' function, found {len(strategy_defs)}"
        raise StrategyParseError(msg, details={"count": len(strategy_defs)})

    fn = strategy_defs[0]
    args = fn.args.args
    if len(args) != 1 or args[0].arg != "df":
        received = ", ".join(a.arg for a in args) or "(none)"
        msg = "Function signature must be 'def strategy(df)'"
        raise StrategyParseError(
            msg,
            details={"expected": "def strategy(df)", "received": f"def strategy({received})"},
        )


def _call_claude(client: Anthropic, description: str) -> str:
    """Call Claude and return the raw text. Wraps network errors in ``ModelUnavailable``."""
    try:
        response = client.messages.create(
            model=settings.quantforge_claude_model,
            max_tokens=settings.quantforge_claude_max_tokens,
            temperature=settings.quantforge_claude_temperature,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": description}],
        )
    except Exception as exc:
        msg = f"Anthropic API unreachable for Strategy Architect: {exc}"
        raise ModelUnavailable(msg) from exc

    blocks = getattr(response, "content", []) or []
    parts: list[str] = []
    for block in blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    joined = "".join(parts).strip()
    if not joined:
        msg = "Strategy Architect received an empty response from Claude"
        raise StrategyParseError(msg)
    return joined


def architect(description: str, *, client: Any) -> StrategyCode:
    """Transform an English strategy description into validated Python source.

    Args:
        description: User's plain-English strategy description.
        client: An ``anthropic.Anthropic`` instance (injected for tests).

    Returns:
        A ``StrategyCode`` containing the validated source and the original
        description.

    Raises:
        StrategyParseError: Generated code failed AST validation.
        ModelUnavailable: Anthropic API was unreachable.
    """
    raw = _call_claude(client, description)
    code = _extract_code_block(raw)
    _validate_ast(code)
    return StrategyCode(source=code, description=description)
