"""Centralized configuration loaded from environment variables.

All runtime settings live here as a single ``Settings`` object. The backend
never reads ``os.environ`` directly — it imports ``settings`` from this module.
This keeps environment handling in one place and makes tests trivially able to
monkey-patch configuration without worrying about process-wide state leaks.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

GeneratorKind = Literal["gbm", "kronos"]


class Settings(BaseSettings):
    """Runtime settings for the QuantForge backend.

    Values are loaded in priority order: process environment, ``.env`` file,
    defaults. Every field has a safe default so the service can boot without a
    ``.env`` file for smoke tests. Only ``anthropic_api_key`` is required for
    real Claude calls; mocked tests ignore it.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    # Claude / Anthropic
    anthropic_api_key: str = Field(default="", description="Anthropic API key; empty in tests.")
    quantforge_claude_model: str = Field(
        default="claude-opus-4-6",
        description="Claude model ID used by all LLM agents.",
    )
    quantforge_claude_temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    quantforge_claude_max_tokens: int = Field(default=2048, ge=128, le=8192)

    # Server
    quantforge_host: str = Field(default="127.0.0.1")
    quantforge_port: int = Field(default=8000, ge=1, le=65535)
    quantforge_log_level: str = Field(default="INFO")
    quantforge_cors_origins: str = Field(default="http://localhost:3000")

    # Pipeline
    quantforge_generator: GeneratorKind = Field(default="gbm")
    quantforge_n_scenarios: int = Field(default=200, ge=20, le=1000)
    quantforge_exec_timeout: float = Field(default=5.0, ge=0.5, le=60.0)
    quantforge_n_variants: int = Field(default=10, ge=2, le=20)

    @field_validator("quantforge_log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            msg = f"log level must be one of {sorted(allowed)}, got {value!r}"
            raise ValueError(msg)
        return upper

    @property
    def cors_origins(self) -> list[str]:
        """Comma-separated CORS origins parsed into a list."""
        return [
            origin.strip() for origin in self.quantforge_cors_origins.split(",") if origin.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    Using ``lru_cache`` means the ``.env`` file is parsed once per process.
    Tests that need to override settings should call ``get_settings.cache_clear()``
    after monkey-patching environment variables.
    """
    return Settings()


settings = get_settings()
