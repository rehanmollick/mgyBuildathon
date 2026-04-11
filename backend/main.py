"""FastAPI application: HTTP surface for the QuantForge pipeline.

Wires pydantic validation, CORS, structured logging, and the four endpoints
(``/api/forge``, ``/api/evolve``, ``/api/narrate``, ``/api/health``). Keep
this file thin: all business logic lives in ``backend/orchestrator.py`` and
the agent modules.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, cast

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import __version__, orchestrator
from backend.config import settings
from backend.exceptions import QuantForgeError
from backend.logging_setup import configure_logging, get_logger
from backend.models import (
    ErrorDetail,
    ErrorResponse,
    EvolveRequest,
    EvolveResult,
    ForgeRequest,
    ForgeResult,
    HealthResponse,
    NarrateRequest,
    NarrateResponse,
)

configure_logging()
log = get_logger(__name__)

_START_TIME = time.time()


def _make_client() -> Any:
    """Construct the default Anthropic client at request time.

    Isolated in a helper so tests can monkey-patch it with a mock. The client
    is lightweight enough to construct per-request; caching it would save a
    microsecond but complicate test isolation.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return None
    if not settings.anthropic_api_key:
        return None
    return Anthropic(api_key=settings.anthropic_api_key)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan: log startup and shutdown."""
    log.info("server.start", version=__version__, generator=settings.quantforge_generator)
    yield
    log.info("server.stop")


app = FastAPI(
    title="QuantForge API",
    description="Six-agent trading strategy stress-testing backend.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)


@app.exception_handler(QuantForgeError)
async def quantforge_exception_handler(
    _request: Request,
    exc: QuantForgeError,
) -> JSONResponse:
    """Convert QuantForgeError into a structured error response."""
    envelope = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id="req_error",
        )
    )
    return JSONResponse(status_code=exc.http_status, content=envelope.model_dump())


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health and configuration metadata."""
    anthropic_available = bool(settings.anthropic_api_key)
    return HealthResponse(
        status="ok",
        version=__version__,
        generator=settings.quantforge_generator,
        anthropic_available=anthropic_available,
        kronos_available=False,
        uptime_seconds=int(time.time() - _START_TIME),
    )


@app.post("/api/forge", response_model=ForgeResult)
async def forge_endpoint(request: ForgeRequest) -> ForgeResult:
    """Run the full Forge pipeline for a user-supplied strategy description."""
    client = _make_client()
    return cast(ForgeResult, orchestrator.forge(request, client=client))


@app.post("/api/evolve", response_model=EvolveResult)
async def evolve_endpoint(request: EvolveRequest) -> EvolveResult:
    """Run the Evolve pipeline, producing a ranked list of mutated variants."""
    client = _make_client()
    return cast(EvolveResult, orchestrator.evolve(request, client=client))


@app.post("/api/narrate", response_model=NarrateResponse)
async def narrate_endpoint(request: NarrateRequest) -> NarrateResponse:
    """Synthesize a verdict into spoken audio (stubbed in v1)."""
    return cast(NarrateResponse, orchestrator.narrate(request))
