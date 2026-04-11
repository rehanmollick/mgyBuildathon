"""Typed exceptions used across the QuantForge pipeline.

Each exception maps one-to-one with an ``ErrorCode`` in the API contract
(see ``docs/API.md``). The FastAPI exception handlers in ``main.py`` convert
these to structured JSON responses with the correct HTTP status.

Never raise bare ``Exception`` or ``RuntimeError`` inside the pipeline — every
failure mode should correspond to a ``QuantForgeError`` subclass so the
frontend can render a specific, actionable message.
"""

from __future__ import annotations

from typing import Any


class QuantForgeError(Exception):
    """Base class for every error the QuantForge pipeline can raise.

    Attributes:
        code: Stable string code matching the API contract.
        message: Human-readable message safe to show to end users.
        details: Optional structured context for debugging.
    """

    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class StrategyParseError(QuantForgeError):
    """The Strategy Architect could not produce valid Python from the description."""

    code = "STRATEGY_PARSE_ERROR"
    http_status = 400


class StrategyExecutionError(QuantForgeError):
    """The user's strategy raised an exception during backtesting."""

    code = "STRATEGY_EXECUTION_ERROR"
    http_status = 400


class StrategyTimeout(QuantForgeError):
    """The user's strategy exceeded the execution timeout."""

    code = "STRATEGY_TIMEOUT"
    http_status = 400


class InvalidAssetError(QuantForgeError):
    """The requested asset ticker is not supported."""

    code = "INVALID_ASSET"
    http_status = 400


class ModelUnavailable(QuantForgeError):
    """An upstream model (Claude, Kronos, VibeVoice) is not reachable."""

    code = "MODEL_UNAVAILABLE"
    http_status = 503


class RateLimited(QuantForgeError):
    """Rate limit exceeded."""

    code = "RATE_LIMITED"
    http_status = 429


class ValidationError(QuantForgeError):
    """Request failed schema validation beyond what pydantic catches."""

    code = "VALIDATION_ERROR"
    http_status = 422
