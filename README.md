# QuantForge

> Every backtest is a lie. It tests one history, the one that happened. QuantForge tests a thousand histories that could have.

[![CI](https://img.shields.io/badge/CI-green-00FF88)](./.github/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-≥80%25-00FF88)](./docs/TESTING.md)
[![mypy](https://img.shields.io/badge/mypy-strict-4C9EFF)](./pyproject.toml)
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-4C9EFF)](./frontend/tsconfig.json)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

QuantForge is a trading strategy stress-testing platform. You describe a strategy in plain English. A six-agent AI pipeline parses it into executable Python, imagines two hundred synthetic market histories with a financial foundation model, runs your strategy against every one of them, and tells you whether your edge is real or just survivorship bias wearing a suit.

## The problem it solves

Traditional backtesting tests your strategy against one history: the one that actually happened. That history happened once. You don't know whether your 40% return is genuine alpha or a lucky path through a distribution of outcomes you never got to see.

QuantForge generates the distribution. If your strategy returns 40% in the real history but loses money in 873 out of 1,000 imagined alternatives, you are not investing. You are gambling. The overfitting percentile tells you the difference in one number.

## Architecture

Six specialized agents, one orchestrator, zero framework code.

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ 1. Strategy      │   │ 2. Market        │   │ 3. Backtester    │
│    Architect     │──▶│    Imaginer      │──▶│    (pure compute)│
│    (Claude)      │   │    (GBM/Kronos)  │   │                  │
│    English → Py  │   │    → 200 markets │   │    → metrics     │
└──────────────────┘   └──────────────────┘   └────────┬─────────┘
                                                       │
                       ┌──────────────────┐   ┌────────▼─────────┐
                       │ 5. Narrator      │◀──│ 4. Analyst       │
                       │    (VibeVoice)   │   │    (Claude)      │
                       │    text → audio  │   │    → verdict     │
                       └──────────────────┘   └──────────────────┘

             Evolve flow adds one agent:
             ┌──────────────────┐
             │ 6. Mutator       │──▶ 10 variants reuse the same
             │    (Claude)      │    market set (Kronos called once)
             └──────────────────┘
```

Read [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for the full system diagram, data flow, and per-agent contracts.

## Tech stack

| Layer    | Choice                                                      |
|----------|-------------------------------------------------------------|
| Frontend | Next.js 15 (App Router), TypeScript strict, Tailwind, Recharts |
| Backend  | FastAPI, Pydantic v2, structlog, asyncio                    |
| Models   | Anthropic Claude, Kronos-mini (alternate), GBM (primary)    |
| Quality  | mypy strict, ruff, black, pytest, vitest, pre-commit hooks  |
| CI       | GitHub Actions on every commit                              |

## Quick start

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Full setup including environment variables, model provisioning, and troubleshooting lives in [`docs/SETUP.md`](./docs/SETUP.md).

## Scope

**v1 (shipping):** Forge tab (stress-test a single strategy) and Evolve tab (mutate a strategy into ten variants, rank by overfitting percentile). Two real routes, two real user flows.

**v2 (roadmap):** Arena (head-to-head strategies), Regimes (regime-conditioned stress testing), Live (real-time Binance feed with on-the-fly prediction bands). See [`docs/ROADMAP.md`](./docs/ROADMAP.md).

## Documentation

| Doc | What it covers |
|-----|----------------|
| [VISION.md](./docs/VISION.md) | The thesis, the market, the long-term bet |
| [PROBLEM.md](./docs/PROBLEM.md) | Why overfitting is invisible and expensive |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System diagram, agent contracts, data flow |
| [TECHNICAL.md](./docs/TECHNICAL.md) | Deep dive on each agent and the math |
| [USER_STORIES.md](./docs/USER_STORIES.md) | Four personas, four flows |
| [ROADMAP.md](./docs/ROADMAP.md) | v1, v2, v3, v4 phases |
| [COMPETITIVE.md](./docs/COMPETITIVE.md) | QuantForge vs QuantConnect, Backtrader, walk-forward, Monte Carlo |
| [TEAM.md](./docs/TEAM.md) | Who is building this and why |
| [SETUP.md](./docs/SETUP.md) | Local dev setup, env vars, model provisioning |
| [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | Common failures and fixes |
| [API.md](./docs/API.md) | Every endpoint, request/response schema, error codes |
| [TESTING.md](./docs/TESTING.md) | Coverage policy, fixtures, what's mocked |
| [SECURITY.md](./docs/SECURITY.md) | safe_exec, secrets, input validation |
| [SCHEMA.md](./docs/SCHEMA.md) | Typed JSON contract between backend and frontend |
| [adr/001-multi-agent-architecture.md](./docs/adr/001-multi-agent-architecture.md) | Why functional modules, not a `BaseAgent` framework |
| [adr/002-gbm-as-primary-generator.md](./docs/adr/002-gbm-as-primary-generator.md) | Why GBM is primary, Kronos alternate |

## License

MIT. See [LICENSE](./LICENSE).
