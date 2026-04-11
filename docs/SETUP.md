# SETUP

Running QuantForge locally takes about five minutes on a machine that already has Python 3.10+ and Node 18+. This document walks through every step, from cloning the repo to making your first `/api/forge` request.

## Prerequisites

- **Python 3.10 or newer.** `python3 --version` should print `3.10.x` or higher. If not, install via `pyenv`, `uv`, Homebrew, or your system package manager.
- **Node.js 18.17 or newer.** `node --version` should print `v18.17.0` or higher. Install via `nvm`, `fnm`, or your system package manager.
- **Git.** Any recent version.
- **An Anthropic API key** (optional for local development with mocks, required for real LLM calls). Get one at https://console.anthropic.com.
- **About 500 MB of free disk space** for Python and Node dependencies.

## Clone and configure

```bash
git clone https://github.com/rehanmollick/mgyBuildathon.git quantforge
cd quantforge
cp .env.example .env
```

Open `.env` in an editor and set at least the `ANTHROPIC_API_KEY` if you want real LLM calls. All other values have sensible defaults.

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev]"
```

This installs the backend as an editable package with all dev dependencies: FastAPI, pydantic, anthropic, structlog, pytest, mypy, ruff, black, hypothesis, and the scientific Python stack.

Verify the install by running the tests:

```bash
pytest
```

Expected output: all tests pass, coverage is at least 80%.

Verify type safety:

```bash
mypy .
```

Expected output: no errors.

Start the backend server:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The server is now listening on `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` in a browser to see the FastAPI-generated Swagger UI.

Hit the health endpoint to confirm everything is wired:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "generator": "gbm",
  "anthropic_available": true
}
```

## Frontend setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend is now running on `http://127.0.0.1:3000`. Open it in a browser.

If the backend is not running or is on a different port, the frontend will show a warning and fall back to mock data from `src/lib/api.ts`. This is intentional for local UI development without needing a full backend.

## Environment variables

All environment variables are documented in `.env.example`. The relevant ones:

| Variable                     | Required | Default            | Description |
|------------------------------|----------|--------------------|-------------|
| `ANTHROPIC_API_KEY`          | partial  | none               | Required for real LLM agents; optional if you only use mocked tests and GBM generator |
| `QUANTFORGE_CLAUDE_MODEL`    | no       | `claude-opus-4-6`  | Which Claude model to use for Architect, Analyst, Mutator agents |
| `QUANTFORGE_GENERATOR`       | no       | `gbm`              | Market Imaginer: `gbm` (default) or `kronos` (alternate, requires weights) |
| `QUANTFORGE_HOST`            | no       | `127.0.0.1`        | Backend bind address |
| `QUANTFORGE_PORT`            | no       | `8000`             | Backend port |
| `QUANTFORGE_CORS_ORIGINS`    | no       | `http://localhost:3000` | Comma-separated list of allowed CORS origins |
| `QUANTFORGE_LOG_LEVEL`       | no       | `INFO`             | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `QUANTFORGE_N_SCENARIOS`     | no       | `200`              | Default number of synthetic market scenarios per stress test |
| `QUANTFORGE_EXEC_TIMEOUT`    | no       | `5.0`              | Seconds before `safe_exec` terminates a runaway strategy |

## First stress test

With both servers running:

1. Open `http://127.0.0.1:3000` in a browser.
2. Type a strategy description into the text box: *"Buy when the 50-day moving average crosses above the 200-day, sell on the cross below."*
3. Click Forge.
4. Wait about fifteen seconds. The ProgressSteps indicator animates through Parse → Imagine → Test → Analyze.
5. The dashboard populates with a fan chart, histograms, gauges, and a verdict.

If something goes wrong, check the browser console for errors, the backend terminal for exceptions, and `docs/TROUBLESHOOTING.md` for known issues.

## Running tests

**Backend tests:**

```bash
cd backend
pytest                          # run full suite with coverage
pytest -n auto                  # parallel with pytest-xdist
pytest tests/test_backtester.py # single file
pytest -k "test_sharpe"         # by name pattern
pytest --cov-report=html        # HTML coverage report at htmlcov/index.html
```

**Frontend tests:**

```bash
cd frontend
npm test                 # run once
npm run test:watch       # watch mode
```

**Type checking:**

```bash
cd backend && mypy .
cd frontend && npm run typecheck
```

**Linting:**

```bash
cd backend && ruff check .
cd backend && black --check .
cd frontend && npm run lint
cd frontend && npm run format:check
```

## Pre-commit hooks

We use pre-commit to catch issues before they reach CI. Install once:

```bash
pip install pre-commit
pre-commit install
```

Now every commit runs ruff, black, trailing whitespace, end-of-file fixer, YAML/JSON validation, and file size checks. If a hook fails, the commit is aborted. Fix the issue and commit again.

To run hooks manually on all files:

```bash
pre-commit run --all-files
```

## Common issues

See `docs/TROUBLESHOOTING.md` for a full list. A few of the most common:

- **`ModuleNotFoundError: No module named 'quantforge'`** — you forgot to activate the virtualenv or forgot `pip install -e ".[dev]"`. Reinstall and try again.
- **`anthropic.APIConnectionError`** — check that `ANTHROPIC_API_KEY` is set in `.env` and that your network allows outbound HTTPS to `api.anthropic.com`. For local testing without an API key, set `QUANTFORGE_GENERATOR=gbm` and use only GBM-based tests; the Architect/Analyst/Mutator agents will need to be mocked in your tests if you don't have a key.
- **Frontend `Module not found: Can't resolve '@/components/...'`** — the `@/` alias is configured in `tsconfig.json` and should just work. If it doesn't, make sure you are running `npm run dev` from the `frontend/` directory.
- **CORS errors in the browser** — set `QUANTFORGE_CORS_ORIGINS=http://localhost:3000` in `.env` and restart the backend.

## Deploying

v1 is built to run locally or on a single host. A Dockerfile and a simple Procfile are provided for quick deployment to Heroku, Railway, Render, or similar. See `docs/TROUBLESHOOTING.md#deploying-to-production` for the current notes.

v2 will include a proper container build with multi-stage optimization, a Kubernetes deployment manifest, and documentation for running on AWS ECS or GCP Cloud Run.

## Developer workflow

The day-to-day loop:

1. Pull latest main.
2. Create a branch with a descriptive name: `git checkout -b feat/evolve-leaderboard`.
3. Make changes. Run tests continuously with `pytest-watch` or `npm run test:watch`.
4. Commit frequently with conventional commit messages: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
5. Push the branch and open a pull request. CI runs automatically.
6. Merge when CI is green and the review is complete.

The goal is that every commit is small, tested, and landable. See `CONTRIBUTING.md` for the full contribution guide.
