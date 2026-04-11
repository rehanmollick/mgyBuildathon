# TESTING

QuantForge treats tests as load-bearing. The Backtester, the stats module, and the orchestrator have tests that would catch any regression before it reaches CI. LLM calls are mocked. External services are mocked. Property tests exercise numerical code. This document explains the coverage policy, the fixture strategy, and what is tested versus mocked.

## Coverage policy

**Backend target:** 80% line coverage minimum, enforced by `pytest --cov-fail-under=80`. If coverage drops below 80%, CI fails, the commit is rejected, and the developer is expected to add tests before re-submitting.

**Frontend target:** meaningful tests on library utilities (formatting, percentile calculations, color helpers) and on key interactive components (RuinGauge, OverfitGauge, LeaderboardTable). We do not chase 80% coverage on the frontend because a large fraction of the code is visual markup where unit tests produce false confidence rather than useful signal. Vitest runs as part of CI, so any broken component test blocks the merge.

**What is excluded from coverage:** `tests/` (obviously), `main.py` (entry point with uvicorn config that is validated by the Next.js build), and `agents/market_imaginer_kronos.py` (requires real Kronos weights, exercised separately in v2).

## Test philosophy

### Test the hard parts, not every line

The Backtester is a compute-heavy state machine. It gets exhaustive tests with known inputs and known outputs. If the Backtester is wrong, every metric in the product is wrong, so we would rather over-test it than under-test it.

The Strategy Architect is a Claude call wrapped in validation. We mock Claude's response and test the validation logic, not the LLM itself. Testing the LLM's output is a fool's errand because the output is non-deterministic and the quality is best measured end-to-end, not unit.

The orchestrator is a thirty-line file that composes agents. We test it end-to-end with every agent mocked so we can assert the composition is correct and the error paths fire the right exceptions.

### Mock at the boundary, not inside

We mock the `anthropic.Anthropic` client at the module boundary in tests. Every agent that calls Claude gets a fixture that returns a canned response. This keeps tests fast (zero network), deterministic (zero LLM variability), and focused on the agent's logic rather than Claude's quirks.

We do not mock `pandas`, `numpy`, or `scipy`. Those are the substrate we rely on, and mocking them would mean testing the mock rather than the code.

### Property tests for numerical code

The GBM generator is tested with Hypothesis property-based tests. Given any valid volatility and drift, the generator must:

- Return exactly `n_scenarios` DataFrames.
- Each DataFrame must have exactly `n_steps` rows.
- All close prices must be positive.
- All high prices must be >= close, open, and low.
- Under a fixed seed, two runs must produce bit-identical outputs.

The stats module is tested against SciPy ground truth. Any metric we compute (Sharpe, max drawdown, percentile-of-score) is also computed via the canonical SciPy implementation and we assert equality to within `1e-10`. This catches transcription errors in the formulas without retesting the math.

### Golden schema tests

The `/api/forge` and `/api/evolve` response schemas are tested via a pydantic round-trip: we construct a `ForgeResult` with canned data, serialize it to JSON, re-parse it, and assert equality. If the schema drifts without us noticing, the round-trip fails and the frontend contract stays aligned with the backend contract. This one test has caught more real bugs than any other single test in the suite.

## Fixture strategy

**Where fixtures live:** `backend/tests/conftest.py` for shared fixtures, per-file fixtures for test-specific setup.

**Key fixtures:**

- `ohlcv_df` — a 500-row pandas DataFrame with realistic OHLCV data derived from a fixed-seed GBM process. Used as input to Backtester tests.
- `real_spy_window` — a pinned slice of real SPY data (2023-H2) for the "real market" backtest path. Committed as a CSV fixture so tests do not depend on yfinance.
- `mock_anthropic` — a pytest fixture that patches `anthropic.Anthropic` with a `MagicMock`. Test code sets the return value per test case.
- `mock_kronos` — a pytest fixture that patches the `market_imaginer_kronos` module's Kronos singleton. Used in Kronos tests to assert the typed interface works without needing real weights.
- `simple_strategy_code` — a string containing a buy-and-hold strategy. Used as the canonical "known good" strategy for Backtester tests.
- `runaway_strategy_code` — a string containing `while True: pass`. Used to test the `safe_exec` timeout path.

## What is tested

### Agent 1: Strategy Architect (`tests/test_strategy_architect.py`)

- Happy path: Claude returns valid code, the agent parses it, returns a `StrategyCode`.
- Invalid function signature (e.g., `def my_strategy(df, extra):`) — raises `StrategyParseError`.
- Disallowed imports (e.g., `import requests`) — raises `StrategyParseError`.
- Syntax errors in returned code — raises `StrategyParseError`.
- Empty response from Claude — raises `StrategyParseError`.
- Network error from Claude — raises `ModelUnavailable`.

### Agent 2: Market Imaginer (GBM) (`tests/test_market_imaginer.py`)

- Returns exactly `n_scenarios` DataFrames.
- Each DataFrame has exactly `n_steps` rows.
- Under a fixed seed, two calls return identical output.
- Property test: high >= max(open, close, low), low <= min(open, close, high), all positive prices.
- Calibration: generator volatility is within 10% of the calibration input's empirical volatility.
- Determinism: passing the same seed twice produces bit-identical output.
- Randomness: passing different seeds produces different output.

### Agent 2 alternate: Kronos (`tests/test_market_imaginer_kronos.py`)

- Typed interface matches the `Generator` protocol.
- Mock-based test: when the Kronos singleton is patched to return canned data, the wrapper returns the expected shape.
- Weights-not-found path: raises `ModelUnavailable` with a helpful message.

### Agent 3: Backtester (`tests/test_backtester.py`)

- Buy-and-hold strategy on a flat market returns 0% with no drawdown.
- Buy-and-hold strategy on a rising market returns positive total_return proportional to the market move.
- Buy-and-hold strategy on a falling market returns negative total_return proportional to the market move.
- Strategy that never signals returns 0% and a flat equity curve.
- Strategy that signals every bar performs like buy-and-hold minus transaction friction (we model zero friction in v1).
- `safe_exec` timeout: runaway strategy raises `StrategyTimeout` within `timeout + 1s`.
- `safe_exec` exception: strategy that divides by zero raises `StrategyExecutionError` with the message from the subprocess.
- `safe_exec` signature mismatch: strategy with wrong signature raises `StrategyExecutionError`.
- Percentile bands computed correctly from a known distribution.

### Agent 4: Analyst (`tests/test_analyst.py`)

- Happy path: given a `BacktestResult`, calls Claude with a prompt containing the metrics, returns the verdict.
- The prompt includes the real total return, synthetic median, and overfitting percentile.
- Network error — raises `ModelUnavailable`.

### Agent 5: Narrator (`tests/test_narrator.py`)

- v1 stub: returns a pre-recorded audio URL deterministically per verdict text hash.
- v2 (skipped): live VibeVoice synthesis returns an audio URL.

### Agent 6: Strategy Mutator (`tests/test_mutator.py`)

- Happy path: Claude returns 10 variants as JSON, agent parses and validates each.
- Invalid variant (e.g., wrong signature) — dropped silently and logged, does not break the run.
- Fewer than `n_variants` valid variants returned — agent re-prompts for replacements up to a cap.
- Network error — raises `ModelUnavailable`.

### Stats module (`tests/test_stats.py`)

- Sharpe ratio: matches SciPy's computation to 1e-10.
- Max drawdown: matches a known closed-form result for a toy equity curve.
- Probability of ruin: returns correct fraction for a known distribution.
- Overfitting percentile: matches `scipy.stats.percentileofscore` to 1e-10.
- Edge case: zero-volatility equity curve returns NaN or 0 for Sharpe (documented behavior).
- Edge case: empty list raises ValueError.

### Orchestrator (`tests/test_orchestrator.py`)

- `forge` calls all five forge agents in the right order.
- `forge` passes the right data between agents (architect output becomes backtester input).
- `forge` raises the right exception on any agent failure.
- `evolve` calls the mutator once and the backtester `n_variants` times.
- `evolve` reuses the same market set across all variants (verified by asserting the imaginer is called exactly once).
- `evolve` enforces per-variant timeouts.

### API contracts (`tests/test_api_contracts.py`)

- `ForgeRequest` round-trips.
- `ForgeResult` round-trips (the golden schema test).
- `EvolveRequest` and `EvolveResult` round-trip.
- `NarrateRequest` and `NarrateResponse` round-trip.
- Invalid requests fail with helpful pydantic error messages.

### Main FastAPI app (`tests/test_main.py`)

- `/api/health` returns 200 with the expected shape.
- `/api/forge` happy path returns 200.
- `/api/forge` with missing `description` returns 422 with a pydantic validation error.
- `/api/forge` when Anthropic is unavailable returns 503 with `MODEL_UNAVAILABLE`.
- `/api/forge` when strategy times out returns 400 with `STRATEGY_TIMEOUT`.
- CORS headers are set correctly for an allowed origin.
- CORS rejects a disallowed origin.

## What is NOT tested in v1

- **Real Claude calls.** Mocked everywhere. Adding real Claude integration tests is a v2 concern because they are flaky, slow, and API-rate-limited.
- **Real Kronos inference.** Mocked everywhere in v1 because the weights are not shipped with the repo. v2 adds smoke tests that run only when the weights are present.
- **Browser end-to-end tests.** v1 has Vitest component tests but no Playwright or Cypress tests. v2 adds Playwright for the Forge flow.
- **Load testing.** v1 is single-user. v2 adds load tests for the FastAPI layer.

## Running the tests

```bash
cd backend
pytest                              # full suite, fails under 80% coverage
pytest -n auto                      # parallel via pytest-xdist
pytest tests/test_backtester.py -v  # specific file, verbose
pytest -k "sharpe"                  # tests with "sharpe" in the name
pytest --cov-report=html            # HTML coverage report at htmlcov/
```

```bash
cd frontend
npm test                            # vitest run
npm run test:watch                  # watch mode
```

## Flake watch

Any test that fails intermittently is a flake. We fix flakes on sight, never mark them as `skip` or `xfail`. A flake is a real bug that happens to manifest occasionally, and leaving it in the suite erodes trust in the entire suite. The three most common flake causes we have hit:

1. **Floating-point equality.** Fix: use `pytest.approx` or assert within tolerance.
2. **Timezone dependence.** Fix: set `TZ=UTC` in the fixture and all test inputs.
3. **Subprocess timing.** Fix: give the subprocess extra margin (e.g., assert timeout is within `[timeout, timeout + 1.0]`).

## Adding tests when adding features

Every PR that adds a feature must add tests for it. The code review will reject a feature-adding PR with no corresponding test additions unless the feature is purely cosmetic (CSS change, markdown doc update).

When adding a new agent, add a test file in `tests/` that covers at least: happy path, one error case per custom exception the agent raises, and a schema validation test for any new pydantic models.
