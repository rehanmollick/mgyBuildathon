"""Tests for the Strategy Mutator agent."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.agents.mutator import mutate
from backend.exceptions import ModelUnavailable


def _resp(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[SimpleNamespace(text=text, type="text")])


def _mock(text: str) -> MagicMock:
    m = MagicMock()
    m.messages.create.return_value = _resp(text)
    return m


_VALID_CODE = (
    "import pandas as pd\\n"
    "def strategy(df):\\n"
    "    s = pd.Series(0, index=df.index)\\n"
    "    s.iloc[0] = 1\\n"
    "    return s"
)


def test_happy_path_returns_variants() -> None:
    body = (
        "[\n"
        f'  {{"description": "V1", "code": "{_VALID_CODE}"}},\n'
        f'  {{"description": "V2", "code": "{_VALID_CODE}"}}\n'
        "]"
    )
    variants = mutate("baseline", 2, client=_mock(body))
    assert len(variants) == 2
    assert variants[0].description == "V1"
    assert "def strategy" in variants[0].code.source


def test_invalid_variants_are_dropped() -> None:
    invalid_code = (
        "import requests\\n"
        "def strategy(df):\\n"
        "    return None"
    )
    body = (
        "[\n"
        f'  {{"description": "bad", "code": "{invalid_code}"}},\n'
        f'  {{"description": "good", "code": "{_VALID_CODE}"}}\n'
        "]"
    )
    variants = mutate("baseline", 2, client=_mock(body))
    assert len(variants) == 1
    assert variants[0].description == "good"


def test_malformed_json_returns_empty() -> None:
    variants = mutate("baseline", 3, client=_mock("not valid json"))
    assert variants == []


def test_network_error_raises_model_unavailable() -> None:
    client = MagicMock()
    client.messages.create.side_effect = RuntimeError("down")
    with pytest.raises(ModelUnavailable):
        mutate("baseline", 3, client=client)
