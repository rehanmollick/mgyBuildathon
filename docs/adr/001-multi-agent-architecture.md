# ADR 001: Multi-agent architecture as plain functional modules

**Status:** Accepted
**Date:** 2026-04-11
**Deciders:** Rehan Mollick

## Context

QuantForge runs six specialized agents in sequence to convert an English strategy description into a stress-tested verdict:

1. **Strategy Architect** — Claude, NLP → Python code
2. **Market Imaginer** — GBM or Kronos, synthetic OHLCV generation
3. **Backtester** — pure Python compute, signal → portfolio equity
4. **Analyst** — Claude, metrics → narrative verdict
5. **Narrator** — VibeVoice (stubbed in v1), text → audio
6. **Strategy Mutator** — Claude, baseline → 10 variants (Evolve flow only)

Each agent has different inputs, outputs, failure modes, and dependencies. We needed to decide how to structure the code so the agents are easy to reason about, test, and replace.

Two obvious options:

**Option A: framework with a `BaseAgent` class.** Every agent inherits from `BaseAgent`, implements `run(input) -> output`, and is composed via a registry. This is the pattern used by LangChain, AutoGen, CrewAI, and most "agent framework" libraries.

**Option B: plain functional modules.** Each agent is a Python module with a typed function. No inheritance, no registry, no framework. The orchestrator is a thirty-line file that calls each function in order.

## Decision

We chose **Option B**: plain functional modules.

Each agent lives in its own file under `backend/agents/`:

```
backend/agents/
├── strategy_architect.py       # def architect(description: str) -> StrategyCode
├── market_imaginer.py          # def imagine(asset: str, n: int) -> MarketSet
├── market_imaginer_kronos.py   # alternate, same signature
├── backtester.py               # def backtest(code: StrategyCode, markets: MarketSet) -> BacktestResult
├── analyst.py                  # def analyze(result: BacktestResult) -> Verdict
├── narrator.py                 # def narrate(verdict: Verdict) -> AudioRef
├── mutator.py                  # def mutate(code: StrategyCode, n: int) -> list[StrategyCode]
└── stats.py                    # pure math helpers shared across agents
```

The orchestrator (`backend/orchestrator.py`) is literally this:

```python
async def forge(request: ForgeRequest) -> ForgeResult:
    code = await architect(request.description)
    markets = await imagine(request.asset, request.n_scenarios)
    result = backtest(code, markets)
    verdict = await analyze(result)
    return ForgeResult(request_id=new_id(), code=code.source, summary=verdict.summary, result=result, verdict=verdict.text)
```

No class hierarchy. No registry. No framework.

## Rationale

### The framework tax is real and the benefit is zero

Agent frameworks pay for themselves when you need dynamic composition, introspection, or tool-use dispatch. We need none of those. QuantForge's pipeline is static: `architect → imagine → backtest → analyze → narrate`. The order never changes. The wiring never changes. A framework solves problems we don't have and introduces friction we'd rather not pay.

Specifically, `BaseAgent` forces every agent to conform to a least-common-denominator interface, usually `run(input: Any) -> Any`. That turns strongly-typed inputs and outputs into `Any`, defeating mypy's whole point. Every agent either type-casts on entry (noise) or gives up on static types (disaster). We want `architect(description: str) -> StrategyCode` and `imagine(asset: str, n: int) -> MarketSet`, and we want mypy to catch every mistake at the boundary. A shared base class cannot give us that.

### Functional modules are easier to test

Each agent is a function. To test it, you call it with canned inputs and assert on the output. No mocks of base-class internals, no registry patching, no lifecycle hooks. `pytest tests/test_strategy_architect.py` loads the module, patches `anthropic.Anthropic`, and runs the function. The test file is thirty lines.

With a `BaseAgent` framework, you'd be testing the framework as much as the agent. Every test starts with fixture setup that constructs the base class, registers the agent, and mocks the lifecycle. That's testing overhead for no real-world value.

### Replaceability at the module level, not the class level

The Market Imaginer has two implementations: GBM (v1 primary) and Kronos (v2). In a framework world, you'd make them both inherit from `MarketImaginerBase` and select one via a registry or a factory. In our world, they're two files (`market_imaginer.py` and `market_imaginer_kronos.py`) exposing the same function signature. The orchestrator selects at import time based on a config flag:

```python
from backend.config import settings
if settings.generator == "kronos":
    from backend.agents.market_imaginer_kronos import imagine
else:
    from backend.agents.market_imaginer import imagine
```

This is a compile-time switch. No runtime dispatch, no polymorphism, no plugin system. If we need both at the same time (we don't, in v1), we import both and call the right one. It's the same swap behavior with a fraction of the code.

### The orchestrator is a thirty-line file

This is the most important point. A 30-line orchestrator is a file a new contributor can read in 90 seconds and understand completely. A 300-line orchestrator with a framework, a registry, and a lifecycle is not.

The orchestrator is the one file every new contributor needs to understand. Keeping it radically simple is worth a significant amount of "convenience" we'd gain from a framework.

### Claude is great at writing small Python files

Most of QuantForge is generated by Claude in collaboration with the human lead. Claude is best when it can see the whole module in its context window. Small, self-contained files (each agent is ~100-200 lines including docstrings and types) fit this model perfectly. A framework-based agent with inheritance, decorators, and base-class hooks is harder to generate correctly in one pass because the context is spread across multiple files.

## Consequences

**Pros:**
- Every agent is a typed function. mypy strict catches bugs at the boundary.
- Tests are fast and focused (no framework fixture setup).
- The orchestrator is 30 lines and can be read top-to-bottom in under a minute.
- Swapping an implementation (GBM ↔ Kronos) is an import change, not a framework change.
- No new contributors need to learn "the QuantForge agent pattern" because there isn't one — it's just Python.

**Cons:**
- If we later want dynamic agent composition (e.g., a user who builds their own pipeline from the agents), we'll need to introduce some kind of registry. For v1 and v2, we don't need this. If the need ever arises, we can add a thin registry layer on top of the existing functions without rewriting the agents.
- There is no shared lifecycle hook for things like "log start/end of every agent". We currently handle this via `structlog` bindings in each agent's entry point — a bit of duplication, but the duplication is three lines per agent, not thirty.
- A new reader might initially look for a framework and not find one. This is addressed in `docs/ARCHITECTURE.md` by explicitly calling out the non-framework decision.

## Alternatives considered

**LangChain.** Too heavy. Its abstractions solve problems we don't have (tool routing, memory, chains) and its typing is loose. The LangChain chain-of-agents pattern looks elegant in demos and collapses under mypy strict.

**AutoGen (Microsoft).** Same issues as LangChain, plus a focus on multi-agent chat loops which is not our model. Our agents run once, in sequence, not in a conversation.

**CrewAI.** Same category. Designed for "agent teams" with role-playing. Not our use case.

**Custom `BaseAgent` class (no external framework).** The lightest version of Option A. Still forces least-common-denominator typing, still adds a class hierarchy to maintain, still makes tests awkward. Rejected for the same reasons.

**One giant `orchestrator.py` file with all agents inline.** The opposite extreme. Would be ~800 lines, impossible to test individual agents in isolation, and impossible to swap implementations. Rejected because modularity is still useful — we just don't need it at the class level.

## Revisit criteria

We'll revisit this decision if any of the following become true:

- A user or third-party developer needs to register new agents at runtime without editing the orchestrator.
- The number of agents exceeds ~15 and the orchestrator becomes hard to read.
- We need to generate the orchestrator from a graph (e.g., user-defined DAG of agents).

None of these are on the v1, v2, or v3 roadmap. If they land in v4, we'll add a thin registry layer; we will not introduce a framework.
