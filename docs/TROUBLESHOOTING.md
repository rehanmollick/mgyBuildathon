# TROUBLESHOOTING

Things go wrong. This document collects the failure modes we have seen, the diagnosis steps that identified them, and the fixes. If you hit something not listed here, open an issue with reproduction steps so we can add it.

## Backend startup issues

### `ModuleNotFoundError: No module named 'fastapi'`

The virtualenv is not activated or dependencies are not installed.

**Fix:**
```bash
cd backend
source .venv/bin/activate
pip install -e ".[dev]"
```

### `anthropic.APIError: 401 Authentication failed`

Your `ANTHROPIC_API_KEY` is missing, malformed, or revoked.

**Diagnosis:**
```bash
python -c "import os; print('key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

**Fix:**
1. Confirm `.env` contains `ANTHROPIC_API_KEY=sk-ant-...`
2. Confirm the backend is reading `.env` via `python-dotenv` or `pydantic-settings`.
3. Confirm the key is valid by running a minimal script:
   ```python
   from anthropic import Anthropic
   client = Anthropic()
   response = client.messages.create(
       model="claude-opus-4-6",
       max_tokens=10,
       messages=[{"role": "user", "content": "hi"}],
   )
   print(response)
   ```

### `pydantic.ValidationError` at startup

One or more environment variables violate the expected type. For example, `QUANTFORGE_PORT=eight` instead of `QUANTFORGE_PORT=8000`.

**Fix:** check `.env` against `.env.example` and correct any malformed values.

### `Address already in use` on port 8000

Another process is already bound to port 8000.

**Diagnosis:**
```bash
lsof -i :8000
```

**Fix:** kill the offending process, or change `QUANTFORGE_PORT` in `.env` to an unused port and restart.

## Frontend issues

### `npm install` fails with peer dependency conflicts

Some package manager versions are strict about peer dependencies. Next.js 15 and React 19 may not be accepted by older npm.

**Fix:**
```bash
npm install --legacy-peer-deps
```

Upgrade npm to a recent version (`npm install -g npm@latest`) as a longer-term fix.

### Browser shows "Failed to fetch" when calling backend

The backend is not running, or CORS is not configured for the frontend origin.

**Diagnosis:**
1. Confirm the backend is running: `curl http://127.0.0.1:8000/api/health`.
2. Check the browser console for the exact error.

**Fix:**
- Start the backend if it is not running.
- If CORS is the error, add the frontend origin to `QUANTFORGE_CORS_ORIGINS` in `.env` and restart the backend.

### `Hydration failed` React warning

Server-rendered HTML does not match the client-side render, usually because of a component that reads from `window`, `localStorage`, or similar in its initial render.

**Fix:** wrap the offending component in a `useEffect` that runs only on the client, or use Next.js's `dynamic()` import with `ssr: false`.

### Tailwind classes are not applying

The Tailwind content globs in `tailwind.config.ts` do not include the file you're editing.

**Fix:** confirm the file path is matched by the `content` array in `tailwind.config.ts`. Restart `npm run dev` after changing the config.

## Agent failures

### `StrategyParseError: function signature mismatch`

Claude returned code that does not define `def strategy(df)` exactly. Usually because the strategy description was ambiguous or the system prompt was too loose.

**Fix:**
- Rephrase the strategy description with more specific language.
- Check the Architect system prompt in `backend/agents/strategy_architect.py`.
- As a last resort, paste the returned code into a Python file and fix by hand, then submit the corrected code directly.

### `StrategyTimeout: Strategy exceeded 5.0s timeout`

The strategy code ran for longer than `QUANTFORGE_EXEC_TIMEOUT` seconds against the real or synthetic data. Usually an infinite loop or an unbounded comprehension.

**Fix:**
- Increase `QUANTFORGE_EXEC_TIMEOUT` in `.env` if the strategy legitimately needs more time (rare).
- Inspect the returned code for `while True` or unbounded recursion and fix or re-prompt the Architect.

### `BacktestError: zero-length equity curve`

The strategy returned an all-zero signal series, which means no positions were ever taken and no equity was accumulated. Sometimes this is correct (a strategy that never fires), but usually it means the indicator logic is wrong.

**Fix:**
- Check the strategy code: are thresholds sensible? Is the window long enough to produce signals given the backtest duration?
- Try a more aggressive parameter set to confirm the strategy fires at all.

### `ModelUnavailable: generator='kronos' but weights not found`

You set `QUANTFORGE_GENERATOR=kronos` but the Kronos weights are not present on disk or are not downloadable.

**Fix:**
- Revert to GBM for v1: `QUANTFORGE_GENERATOR=gbm`
- For Kronos in v2, run `huggingface-cli download NeoQuasar/Kronos-mini --local-dir checkpoints/Kronos-mini` and confirm the path in the Kronos config.

## Test failures

### `coverage failure: coverage is 78%, fail_under is 80`

Tests are passing but not covering enough code. Either recently added code is untested or an existing test was removed.

**Fix:**
```bash
pytest --cov-report=term-missing
```

Look at the `Missing` column for line numbers that need coverage. Add tests.

### `mypy error: Incompatible types in assignment`

A type annotation does not match the runtime value. Usually a pandas operation that returns `Any` or an Anthropic SDK response whose shape we did not type properly.

**Fix:**
- Read the error carefully. The line number is usually correct.
- If pandas stubs are wrong, use `typing.cast` sparingly to assert the shape.
- If Anthropic SDK types are loose, wrap the response in a `pydantic` model at the boundary.
- Do not suppress with `# type: ignore` unless you can add a specific `[error-code]` and a one-line comment explaining why.

### `pytest: StaleDataError` or `ResourceWarning: unclosed file`

A test fixture is leaking a resource. Usually because a `yield`-style fixture did not finalize correctly.

**Fix:** convert to the `with` context manager pattern inside the fixture, or add explicit teardown via `request.addfinalizer`.

### `hypothesis: Flaky test` on the Backtester property tests

A property test found a shrinking counterexample that fails sometimes and passes other times. Usually because the test depends on floating-point equality or random seed.

**Fix:**
- Use `hypothesis.settings(deadline=None)` if the test is compute-heavy.
- Use `pytest.approx` for floating-point comparisons.
- Seed the RNG explicitly in the strategy or backtest.

## Performance issues

### `/api/forge` takes longer than 30 seconds

One of the agents is stuck or slow. Diagnose per-stage timing from the structlog output.

**Diagnosis:**
```bash
QUANTFORGE_LOG_LEVEL=DEBUG uvicorn main:app
```

Look at the `agent.start` and `agent.end` events for each agent. The slowest one is your culprit.

**Common causes:**
- **Strategy Architect slow:** Claude API latency. Check https://status.anthropic.com.
- **Market Imaginer slow:** GBM should be <1s; Kronos can be 5-15s for 200 scenarios. If GBM is slow, something is wrong with the numpy install.
- **Backtester slow:** the strategy code is computationally expensive. Profile the subprocess target function.
- **Analyst slow:** Claude API latency, see above.

### Memory usage grows over time

Module-level caches (market data, model weights) are not being released. Usually fine, but can bite on long-running servers.

**Fix:** restart the server periodically, or add an LRU cache with a maximum size to `load_real_market` in the backtester.

### `RecursionError` during strategy execution

The strategy code recursed too deeply. Usually a misunderstanding of pandas rolling operations.

**Fix:** increase the subprocess's recursion limit with `sys.setrecursionlimit(10000)` inside `_run_strategy_in_subprocess`, or re-prompt the Architect for an iterative implementation.

## CI issues

### GitHub Actions fails on `pytest` but passes locally

Usually because of an environment difference: Python version, timezone, locale, or an external API that is unavailable in CI.

**Fix:**
- Check the Actions log for the exact failure.
- Pin the Python version in `ci.yml` (we use 3.11).
- Mock any external API calls in tests. Do not depend on network in CI.
- Set `TZ=UTC` in the CI environment if tests depend on timezone.

### GitHub Actions fails on `mypy` but passes locally

Your local `mypy` is an older version. Pin the version in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "mypy==1.9.0",
    ...
]
```

### Cache miss on every CI run

The cache key is not stable. GitHub Actions caches by hash of the lockfile; if you do not have a lockfile, the cache misses every time.

**Fix:** commit a `package-lock.json` for the frontend and use `pip-tools` or `uv lock` for the backend.

## Data issues

### `yfinance` returns empty DataFrame for SPY

yfinance occasionally has outages or rate-limits free users.

**Fix:**
- Retry with exponential backoff.
- Fall back to a committed CSV of historical SPY data in `backend/data/spy_historical.csv`.

### Real-history backtest disagrees with a trusted source

Small disagreements (~0.5%) are usually dividend handling or adjusted-close conventions. Large disagreements (>2%) suggest a bug in the portfolio simulation.

**Fix:** compare the equity curve at each rebalance step against the trusted source. The divergence point is your bug.

## Deploying to production

v1 is built to run as a single process. The recommended deployment target is any PaaS that can run a Python process and a Node process (Railway, Render, Fly.io, Heroku).

Steps:

1. Set all environment variables from `.env.example` in the platform's secrets manager. Do not commit `.env` to the repo.
2. Set `QUANTFORGE_CORS_ORIGINS` to the public frontend URL, not `*`.
3. Use a production ASGI server (`uvicorn` with `--workers 2` or `gunicorn` with `UvicornWorker`).
4. Front the backend with TLS, either via the PaaS's built-in TLS or via a reverse proxy.
5. Configure health checks to hit `/api/health`.
6. Set `QUANTFORGE_LOG_LEVEL=INFO` in production. `DEBUG` is too verbose and may leak sensitive data.

For v2 we ship a Dockerfile and a docker-compose file. See that version's release notes.

## Getting help

Open an issue on the repo with:
- Your OS and Python/Node versions
- The exact error message (copy-paste, not paraphrased)
- The steps to reproduce
- What you have already tried

Do not include your `.env` file or any API keys in issues or commits.
