"""Smoke tests for the FastAPI endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import backend.main as main_module
from backend.main import app


def _resp(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[SimpleNamespace(text=text, type="text")])


_ARCHITECT = (
    "```python\n"
    "import pandas as pd\n"
    "def strategy(df):\n"
    "    s = pd.Series(0, index=df.index)\n"
    "    s.iloc[0] = 1\n"
    "    return s\n"
    "```"
)
_ANALYST = '{"summary": "Ok.", "verdict": "Robust across synthetic runs."}'


@pytest.fixture
def client_with_mock(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Return a FastAPI TestClient with the Anthropic client factory patched."""
    mock = MagicMock()
    mock.messages.create.side_effect = [_resp(_ARCHITECT), _resp(_ANALYST)]
    monkeypatch.setattr(main_module, "_make_client", lambda: mock)
    with TestClient(app) as c:
        yield c


def test_health_returns_200(client_with_mock: TestClient) -> None:
    r = client_with_mock.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["generator"] in ("gbm", "kronos")


def test_forge_happy_path(client_with_mock: TestClient) -> None:
    r = client_with_mock.post(
        "/api/forge",
        json={
            "description": "Buy and hold SPY as the baseline",
            "asset": "SPY",
            "n_scenarios": 20,
            "seed": 1,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["request_id"].startswith("req_")
    assert "def strategy" in body["code"]
    assert "result" in body


def test_forge_rejects_short_description(client_with_mock: TestClient) -> None:
    r = client_with_mock.post(
        "/api/forge",
        json={"description": "bad", "asset": "SPY", "n_scenarios": 20},
    )
    assert r.status_code == 422


def test_narrate_returns_stub_url(client_with_mock: TestClient) -> None:
    r = client_with_mock.post(
        "/api/narrate",
        json={"verdict_text": "Your strategy is robust."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "stub"
    assert body["audio_url"].startswith("/static/audio/")
