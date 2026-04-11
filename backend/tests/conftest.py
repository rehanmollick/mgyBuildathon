"""Shared pytest fixtures for the QuantForge backend test suite."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from backend.agents.market_imaginer import MarketSet, imagine


@pytest.fixture
def ohlcv_df() -> pd.DataFrame:
    """A 252-bar deterministic OHLCV DataFrame for Backtester tests."""
    rng = np.random.default_rng(42)
    n = 252
    idx = pd.bdate_range("2023-01-02", periods=n)
    close = 100.0 * np.exp(np.cumsum(rng.standard_normal(n) * 0.01))
    open_ = close * (1 + rng.standard_normal(n) * 0.002)
    high = np.maximum(open_, close) * (1 + np.abs(rng.standard_normal(n)) * 0.003)
    low = np.minimum(open_, close) * (1 - np.abs(rng.standard_normal(n)) * 0.003)
    volume = rng.integers(1_000_000, 5_000_000, size=n).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )


@pytest.fixture
def market_set() -> MarketSet:
    """A small deterministic MarketSet for pipeline tests."""
    return imagine("SPY", n_scenarios=5, n_steps=60, seed=7)


@pytest.fixture
def simple_strategy_code() -> str:
    """A buy-and-hold strategy: always long from bar 0."""
    return (
        "import pandas as pd\n"
        "import numpy as np\n"
        "def strategy(df):\n"
        "    s = pd.Series(0, index=df.index)\n"
        "    s.iloc[0] = 1\n"
        "    return s\n"
    )


@pytest.fixture
def no_signal_strategy_code() -> str:
    """A strategy that never trades — all-zero signals."""
    return "import pandas as pd\n" "def strategy(df):\n" "    return pd.Series(0, index=df.index)\n"


@pytest.fixture
def runaway_strategy_code() -> str:
    """A strategy that loops forever — used to test timeout enforcement."""
    return (
        "import pandas as pd\n"
        "def strategy(df):\n"
        "    while True:\n"
        "        pass\n"
        "    return pd.Series(0, index=df.index)\n"
    )


def _fake_claude_response(text: str) -> Any:
    """Build a minimal object shaped like an Anthropic Messages response."""
    return SimpleNamespace(content=[SimpleNamespace(text=text, type="text")])


@pytest.fixture
def mock_anthropic_architect() -> MagicMock:
    """MagicMock client whose messages.create returns a buy-and-hold code block."""
    client = MagicMock()
    client.messages.create.return_value = _fake_claude_response(
        "```python\n"
        "import pandas as pd\n"
        "def strategy(df):\n"
        "    s = pd.Series(0, index=df.index)\n"
        "    s.iloc[0] = 1\n"
        "    return s\n"
        "```"
    )
    return client


@pytest.fixture
def mock_anthropic_analyst() -> MagicMock:
    """MagicMock client whose messages.create returns a JSON analyst verdict."""
    client = MagicMock()
    client.messages.create.return_value = _fake_claude_response(
        '{"summary": "Robust.", "verdict": "Your strategy held up under stress."}'
    )
    return client


@pytest.fixture
def mock_anthropic_mutator() -> MagicMock:
    """MagicMock client returning two valid variants."""
    client = MagicMock()
    body = (
        "[\n"
        ' {"description": "Variant A", "code": "import pandas as pd\\ndef strategy(df):\\n    s = pd.Series(0, index=df.index)\\n    s.iloc[0] = 1\\n    return s"},\n'
        ' {"description": "Variant B", "code": "import pandas as pd\\ndef strategy(df):\\n    s = pd.Series(0, index=df.index)\\n    s.iloc[1] = 1\\n    return s"}\n'
        "]"
    )
    client.messages.create.return_value = _fake_claude_response(body)
    return client


@pytest.fixture
def mock_anthropic_all(
    mock_anthropic_architect: MagicMock,
    mock_anthropic_analyst: MagicMock,
) -> MagicMock:
    """A single client that returns architect response then analyst response in sequence."""
    client = MagicMock()
    arch_resp = mock_anthropic_architect.messages.create.return_value
    analyst_resp = mock_anthropic_analyst.messages.create.return_value
    client.messages.create.side_effect = [arch_resp, analyst_resp]
    return client
