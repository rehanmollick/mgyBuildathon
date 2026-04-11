# TEAM

QuantForge is built by a small team that combines deep Python experience, a background in applied machine learning, and real skin in the game trading personal capital. The team's goal is to ship the first product in the Distributional Strategy Stress Testing category and own the narrative around it.

## The builders

### Rehan Mollick — founder, full-stack lead

Rehan leads product, backend architecture, and the overall build. His background spans data infrastructure, applied machine learning, and fintech product work. He has been trading personal capital algorithmically since 2022 and has personally lost money to overfit strategies that looked great in backtesting. The experience is not hypothetical, and it is what drives QuantForge's product choices. If a feature does not help a trader like him avoid the next overfit strategy, the feature gets cut.

Rehan wrote the six-agent architecture, chose GBM as the v1 primary generator after evaluating Kronos's cold-start costs, and is the primary author of the documentation set. He is the decision-maker on scope cuts and the person who decides when to ship.

### The Claude collaborative layer

QuantForge is explicitly built in close collaboration with Claude (Anthropic's LLM), invoked through the Claude Code CLI and through the product's own agent pipeline at runtime. This is not a footnote; it is how the product is built and how the product works in production.

At build time, Claude drafts the majority of documentation content, suggests architecture patterns, catches type errors before they reach CI, and generates the first pass of most Python modules. The human team edits for voice, correctness, and judgment. Claude does not make architectural decisions, but Claude dramatically accelerates the execution of the decisions the team does make.

At runtime, three of the six agents (Strategy Architect, Analyst, Strategy Mutator) are Claude calls with strict system prompts. The product itself is a composition of Claude plus specialized models (Kronos for markets, VibeVoice for audio) orchestrated through a thirty-line Python file. QuantForge is a concrete example of how builders in 2026 should be composing models into products: not as a thin wrapper around one model, but as a specialized pipeline where each model does the thing it is best at.

## Why this team can build this

**Python fluency.** The backend is type-hinted, pydantic-validated, mypy-strict Python. The team has written production Python systems before and knows the difference between code that compiles and code that is safe to ship.

**LLM orchestration experience.** Composing Claude into multi-step pipelines is the kind of work that separates "AI-enabled products" from "products with an AI button." The team has built this before on other projects and knows the pitfalls: prompt injection, hallucinated numbers, inconsistent output schemas, rate limits. The product reflects those scars.

**Algo trading empathy.** The team trades personal capital and has lived the pain of overfit strategies. Product decisions are not derived from first principles; they are derived from experience with the problem. Every feature has a "does this help a trader like me" test.

**Architectural clarity.** The team has read enough abstracted frameworks to know when a framework is the wrong answer. The anti-framework rule (see `adr/001-multi-agent-architecture.md`) is a principled choice, not an accident. It is the kind of choice that compounds: cleaner code is easier to test, easier to document, easier to extend, easier to reason about. The team chose clarity over cleverness at every branch point.

## Why this team cannot build everything

We are honest about our limits. Here is what we will not try to build ourselves in v1:

- **Production-grade intraday tick simulation.** Backtrader and LEAN already do this well. If a user needs tick-level accuracy, they should use a mature backtester and use QuantForge as the distributional stress test on top.
- **Real-time order routing.** We are not a broker. Integration with brokers comes in v3, and only as an API exposing our existing features; we are not going to build order management.
- **Custom candlestick charting libraries.** Recharts is enough for v1. If we need more in v2, we will integrate an existing charting library, not build one.
- **Full compliance and audit infrastructure.** Enterprise compliance features (SOC2, GDPR audit logs, encryption at rest for user strategies) are v4 concerns that require a dedicated compliance engineer. We are not trying to serve enterprise customers in v1.

## The values we build by

- **Ship the insight, not the feature list.** We would rather ship one flow that changes how users think than five flows that each do a small thing.
- **Truth over optimism.** If a metric is ambiguous, we show the ambiguity. If a result is lucky, we say it is lucky. The product is a truth-telling tool and the team behaves accordingly.
- **Boring tech in the hot path.** FastAPI, Pydantic, numpy, pandas, Next.js. We save our innovation budget for the agent composition and the generative market model; we do not spend it on exotic frameworks.
- **Types everywhere.** mypy strict, TypeScript strict. The types are a form of documentation and a form of tests. The team treats a mypy error the same as a failing test: fix it now, not later.
- **Test the hard parts.** We test the Backtester and stats modules exhaustively because they are the compute core. We mock the LLM calls in tests because mocking Claude is fast and deterministic and testing the prompt instead of the response is a fool's errand.
- **Document the why, not the what.** The code says what it does. The docs say why we chose this approach over alternatives and what tradeoffs we accepted. Architecture Decision Records are the canonical form.
- **Commit early and often.** One logical change per commit. Conventional commit messages. A linear history that tells the story of the build.

## How we work with Claude

Claude is invoked through the Claude Code CLI during development for drafting, refactoring, and reviewing. Every commit is still authored by a human who reads the diff, runs the tests, and takes responsibility. Claude is a force multiplier, not a rubber stamp.

At runtime, Claude is accessed through the Anthropic Python SDK with structured system prompts and strict output validation. We do not trust Claude's output implicitly; every response is parsed, validated, and checked for expected shape before it is allowed to reach the next agent in the pipeline. If validation fails, we raise a typed exception and the caller decides whether to retry, fall back, or surface an error to the user.

The team treats Claude the way a software engineer treats a compiler: useful, fast, usually correct, and always subject to verification.

## What the team values in users

We are building for users who:

- **Treat their own code with suspicion.** The best users of QuantForge are the ones who are skeptical of their own backtests and want a tool that can argue with them.
- **Trust numbers more than narrative.** The fan chart and the overfitting percentile are numbers. The verdict text is narrative. Our best users read both.
- **Iterate fast.** Users who take hours between stress tests get less value than users who run fifty tests in an afternoon while they refine their strategy. Speed of iteration is why we ship in under fifteen seconds.
- **Share their failures.** Users who post their fan charts publicly, including the ones showing their strategy is overfit, are our champions. The product is most useful when it is a public truth-telling tool, not a private confidence booster.

## Contact

File issues and feature requests on the public GitHub repository. For enterprise inquiries, reach out via the email listed in `README.md`. For bugs with reproduction steps, use the issue tracker. For everything else, join the discussion.
