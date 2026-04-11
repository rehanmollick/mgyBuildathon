"""Tests for the orchestrator (Forge and Evolve pipelines)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.models import EvolveRequest, ForgeRequest
from backend.orchestrator import evolve, forge


def _resp(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[SimpleNamespace(text=text, type="text")])


_ARCHITECT_CODE = (
    "```python\n"
    "import pandas as pd\n"
    "def strategy(df):\n"
    "    s = pd.Series(0, index=df.index)\n"
    "    s.iloc[0] = 1\n"
    "    return s\n"
    "```"
)

_ANALYST_JSON = '{"summary": "Strong.", "verdict": "Your strategy looks robust."}'


def _multi_step_client(*responses: str) -> MagicMock:
    client = MagicMock()
    client.messages.create.side_effect = [_resp(r) for r in responses]
    return client


def test_forge_happy_path() -> None:
    client = _multi_step_client(_ARCHITECT_CODE, _ANALYST_JSON)
    req = ForgeRequest(
        description="Buy and hold SPY as a baseline",
        asset="SPY",
        n_scenarios=20,
        seed=1,
    )
    result = forge(req, client=client)
    assert result.request_id.startswith("req_")
    assert "def strategy" in result.code
    assert result.summary == "Strong."
    assert result.result.real.equity_curve
    assert 0.0 <= result.result.overfitting_percentile <= 100.0
    assert client.messages.create.call_count == 2


def test_evolve_happy_path() -> None:
    mutator_json = (
        "[\n"
        '  {"description": "A", "code": "import pandas as pd\\ndef strategy(df):\\n    s = pd.Series(0, index=df.index)\\n    s.iloc[0] = 1\\n    return s"},\n'
        '  {"description": "B", "code": "import pandas as pd\\ndef strategy(df):\\n    return pd.Series(0, index=df.index)"}\n'
        "]"
    )
    client = _multi_step_client(
        _ARCHITECT_CODE,    # baseline architect
        _ANALYST_JSON,      # baseline analyst
        mutator_json,       # mutator
    )
    req = EvolveRequest(
        description="Buy and hold SPY as a baseline",
        asset="SPY",
        n_variants=2,
        n_scenarios=20,
        seed=2,
    )
    result = evolve(req, client=client)
    assert result.baseline.code
    assert len(result.variants) == 2
    # Ranks are consecutive starting from 1
    assert [v.rank for v in result.variants] == [1, 2]
