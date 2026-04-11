"""Tests for the Strategy Architect agent."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.agents.strategy_architect import architect
from backend.exceptions import ModelUnavailable, StrategyParseError


def _resp(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[SimpleNamespace(text=text, type="text")])


def _mock(text: str) -> MagicMock:
    m = MagicMock()
    m.messages.create.return_value = _resp(text)
    return m


def test_happy_path_parses_and_returns() -> None:
    code = (
        "```python\n"
        "import pandas as pd\n"
        "def strategy(df):\n"
        "    return pd.Series(0, index=df.index)\n"
        "```"
    )
    result = architect("Buy and hold", client=_mock(code))
    assert "def strategy(df)" in result.source
    assert result.description == "Buy and hold"


def test_syntax_error_raises_parse_error() -> None:
    bad = "def strategy(df):\n    return pd.Series(  # unclosed\n"
    with pytest.raises(StrategyParseError):
        architect("x" * 20, client=_mock(bad))


def test_wrong_signature_raises() -> None:
    bad = (
        "import pandas as pd\n"
        "def strategy(df, extra):\n"
        "    return pd.Series(0, index=df.index)\n"
    )
    with pytest.raises(StrategyParseError, match="signature"):
        architect("test", client=_mock(bad))


def test_disallowed_import_raises() -> None:
    bad = (
        "import requests\n"
        "import pandas as pd\n"
        "def strategy(df):\n"
        "    return pd.Series(0, index=df.index)\n"
    )
    with pytest.raises(StrategyParseError, match="not allowed"):
        architect("test", client=_mock(bad))


def test_missing_strategy_function_raises() -> None:
    bad = "import pandas as pd\nx = 1\n"
    with pytest.raises(StrategyParseError):
        architect("test", client=_mock(bad))


def test_empty_response_raises() -> None:
    with pytest.raises(StrategyParseError):
        architect("test", client=_mock(""))


def test_network_error_raises_model_unavailable() -> None:
    client = MagicMock()
    client.messages.create.side_effect = RuntimeError("connection refused")
    with pytest.raises(ModelUnavailable):
        architect("test", client=client)


def test_unfenced_response_is_parsed() -> None:
    code = "import pandas as pd\n" "def strategy(df):\n" "    return pd.Series(0, index=df.index)\n"
    result = architect("test", client=_mock(code))
    assert "def strategy" in result.source
