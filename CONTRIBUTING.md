# Contributing to QuantForge

QuantForge is an open-source trading strategy stress-testing platform. This
document explains how to set up the project, what quality gates are enforced,
and how to ship a change.

## Quick start

```bash
# Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest

# Frontend
cd frontend
npm install
npm run typecheck
npm test
npm run dev
```

See [docs/SETUP.md](./docs/SETUP.md) for the full setup walkthrough including
Colab, ngrok, and Kronos checkpoints.

## Project layout

- `backend/` — FastAPI app, six agents, orchestrator, tests
- `frontend/` — Next.js 15 app, Forge and Evolve tabs, Recharts dashboards
- `docs/` — Vision, architecture, ADRs, API contract, setup, testing, security
- `.github/workflows/` — CI that runs every gate below on push and PR

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for the full system diagram
and [docs/adr/](./docs/adr/) for decisions we do not plan to revisit casually.

## Quality gates

Every PR must pass every gate. CI runs all of these on GitHub Actions and the
pre-commit hooks run them locally.

### Backend

```bash
cd backend
.venv/bin/ruff check .          # lint (zero warnings)
.venv/bin/mypy .                # strict typing (zero errors)
.venv/bin/pytest                # ≥80% coverage enforced in pyproject.toml
```

Current state: ruff clean, mypy strict clean on 29 source files,
70 tests passing at 92% coverage.

### Frontend

```bash
cd frontend
npm run typecheck               # tsc strict, zero errors
npm test                        # vitest run
npm run build                   # production build compiles
```

Current state: 29 tests passing, typecheck clean, build compiles.

### Pre-commit

`.pre-commit-config.yaml` runs ruff, mypy, and prettier on every commit. Install
with `pre-commit install` after cloning.

## Commit style

We use [conventional commits](https://www.conventionalcommits.org/). The
`type(scope): subject` form is mandatory so the changelog stays readable.

Types we use:

- `feat(backend|frontend|docs)` — new feature
- `fix(backend|frontend)` — bug fix
- `docs` — doc-only change
- `test(backend|frontend)` — test-only change
- `refactor` — no behavior change
- `chore` — tooling, CI, dependency bumps

Keep the subject line under 72 characters, wrap the body at 80. Include a
"Why" section if the change is not self-evident.

## How to add a new agent

QuantForge's architecture treats agents as plain functional modules, not
instances of a `BaseAgent` class. See
[docs/adr/001-multi-agent-architecture.md](./docs/adr/001-multi-agent-architecture.md)
for the rationale. To add a new agent:

1. Create `backend/agents/<name>.py` with a single public function and a
   typed output dataclass.
2. Wire the function into `backend/orchestrator.py`.
3. Add tests in `backend/tests/test_<name>.py`. Mock external clients at the
   function boundary, never at the library level.
4. Update `docs/ARCHITECTURE.md` with the new node in the pipeline diagram.
5. If the agent changes the API contract, update `docs/SCHEMA.md` and the
   TypeScript mirror in `frontend/src/lib/types.ts` in the same commit.

## How to add a new chart

Charts live in `frontend/src/components/`. Every chart card is a wrapper
around `ChartCard` which supplies the dark border, title, and subtitle.

1. Add the component next to its siblings.
2. Mirror any new backend field in `frontend/src/lib/types.ts`.
3. Add a fixture value in `frontend/src/lib/fixtures.ts` so demo mode works
   without a backend.
4. Add a vitest in `frontend/__tests__/components/` that at least asserts
   the component renders with fixture data.

## Reporting security issues

See [docs/SECURITY.md](./docs/SECURITY.md). TL;DR: user-supplied strategy code
runs through `safe_exec` in a subprocess with a wall-clock timeout and a
restricted `__builtins__`. If you find a sandbox escape, open a private
advisory, not a public issue.
