"""Structlog configuration with secret sanitization.

Call ``configure_logging()`` once at application startup. After that, any
module can get a logger via ``structlog.get_logger(__name__)`` and log with
structured key/value fields. The sanitization processor strips any key that
looks like a secret so API keys cannot leak into logs even by accident.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from backend.config import settings

_SECRET_KEY_MARKERS = ("api_key", "apikey", "_key", "_token", "secret", "password", "authorization")


def _sanitize_secrets(_logger: Any, _method_name: str, event_dict: EventDict) -> EventDict:
    """Replace values of secret-like keys with ``"***"``.

    The check is intentionally loose: any key containing a marker string is
    sanitized. False positives are fine; missing a secret is not.
    """
    for key in list(event_dict.keys()):
        lowered = key.lower()
        if any(marker in lowered for marker in _SECRET_KEY_MARKERS):
            event_dict[key] = "***"
    return event_dict


def configure_logging() -> None:
    """Configure structlog and the stdlib root logger.

    The configuration emits JSON in production and key-value pairs in dev,
    determined by whether stdout is a TTY. Log level comes from settings.
    """
    level = getattr(logging, settings.quantforge_log_level, logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _sanitize_secrets,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if sys.stdout.isatty():
        renderer: Processor = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to the caller's module name."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]
