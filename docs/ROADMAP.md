# ROADMAP

QuantForge is shipped in phases. Each phase is scoped so it stands alone as a usable product and so the next phase is a clean additive build rather than a rewrite.

## Phase 1 — v1 (shipping)

**Goal.** Prove the core insight works end-to-end: describe a strategy in English, get a fan chart of alternative histories, see the overfitting percentile, make a better decision.

**Ships with:**

- **Forge tab** — the primary user flow. StrategyInput, ProgressSteps, CodePreview, EquityCurveFan, ReturnHistogram, DrawdownHistogram, SharpeHistogram, RuinGauge, OverfitGauge, VerdictPlayer. End to end in under fifteen seconds per request.
- **Evolve tab** — the mutation search. Takes a baseline strategy, generates ten variants via the Mutator agent, runs all variants against the same 200-market set, and ranks them by overfitting percentile. Leaderboard table is clickable to drill into any variant's full dashboard.
- **Six-agent backend** — Strategy Architect, Market Imaginer (GBM primary), Backtester, Analyst, Narrator (stub audio), Strategy Mutator. All typed, all tested, all documented.
- **FastAPI layer** — `/api/forge`, `/api/evolve`, `/api/narrate`, `/api/health`. Pydantic validation on every request and response.
- **Ten presets** — ten classic strategies preloaded in a dropdown for zero-friction onboarding.
- **GBM primary generator** — fast, deterministic, always available. Calibrated to real SPY volatility.
- **Kronos alternate module** — typed interface, mock-tested, present in the architecture but not the hot path in v1.
- **Documentation** — 16 files in `docs/`, investor-grade.
- **CI green on every commit** — pytest, mypy strict, ruff, black, eslint, tsc, vitest, Next.js build.

**Explicitly NOT in v1:**

- Arena, Regimes, Live tabs (see Phase 2)
- Live Kronos inference (see Phase 2)
- Live VibeVoice narration (see Phase 2)
- PDF export (see Phase 3)
- User accounts, saved strategies, paid tiers (see Phase 3)
- Real-time market data (see Phase 2)

## Phase 2 — v2 (next)

**Goal.** Extend the insight across the remaining tabs and flip the alternate generator to primary. Make the product feel complete.

**Arena tab.** Two strategies head-to-head. Side-by-side fan charts, a "Strategy A wins X/200 scenarios" headline, comparative histograms for returns/drawdowns/Sharpe, a verdict that names the winner and explains why. The shared market set makes this cheap: imagine once, backtest twice.

**Regimes tab.** Same interface as Forge, but with a row of regime buttons above the dashboard: Bull, Bear, Crash, Sideways, High-Volatility. Clicking a regime seeds the Market Imaginer with historical context from that regime type, so the synthetic futures imagined are conditioned on the selected regime. Dashboard shows per-regime distribution panels so the user sees how their strategy performs across all conditions at once.

**Live tab.** Real-time Binance WebSocket for BTC/USDT 1-minute candles. Rolling 512-candle buffer fed to Kronos for live prediction bands. Strategy signals overlaid on the candlestick chart with real-time markers. VibeVoice announces signals aloud. Anomaly indicator when the current price diverges significantly from Kronos's prediction band.

**Live Kronos inference.** Flip the Market Imaginer from GBM primary to Kronos primary. GBM remains as the fallback when Kronos weights are unavailable. Document the performance and realism differences between the two generators.

**Live VibeVoice narration.** Replace the stub audio with fresh VibeVoice synthesis per request. Cache per verdict-text hash to avoid re-synthesizing repeated verdicts.

**Ten more preset strategies.** Adding options strategies, pairs trades, and volatility strategies to the preset dropdown.

**Multi-asset support.** Beyond SPY, add AAPL, MSFT, NVDA, BTC, ETH, SPY, QQQ, TLT, GLD. Each asset gets a pinned historical data window for the real backtest.

## Phase 3 — paid tier

**Goal.** Monetize. Build the account layer, the billing layer, and the features that unlock paid usage.

**User accounts.** Email signup, OAuth with Google and GitHub. Saved strategies in a personal library. Strategy versioning.

**Paid tier** at $30/month for individuals. Includes unlimited Forge/Evolve runs, saved strategy history, strategy sharing via URL, PDF export.

**Team tier** at $500/month for small quant teams. Includes the individual tier plus API access, team-shared strategy library, and audit logs.

**Enterprise tier** custom-priced for hedge funds and prop shops. Includes SSO, on-premise deployment, custom model fine-tuning, dedicated support.

**PDF export.** Professional PDF reports with the full dashboard embedded, suitable for sharing with investment committees or teaching. Triggered from any dashboard via a single click.

**Strategy sharing.** Publish any strategy result as a public URL. Viewers see the dashboard without needing an account. Shares include an anti-spoofing hash so the original metrics cannot be modified.

**Strategy libraries.** Curated public libraries of strategies organized by category (momentum, mean reversion, breakout, volatility) with peer-reviewed overfitting percentiles.

## Phase 4 — platform

**Goal.** Generalize QuantForge beyond trading. The six-agent architecture is applicable to any system that needs distributional stress-testing.

**Kronos fine-tunes per asset class.** Separate fine-tuned weights for equities, FX, commodities, crypto. Each tune reflects the specific distributional properties of its asset class.

**Custom generator API.** Bring-your-own generative model. Expose a `Generator` protocol so customers can plug in their own market simulator while using QuantForge's Backtester, Analyst, and dashboard infrastructure.

**Risk manager wedge.** Adjacent vertical. Portfolio-level stress testing for wealth advisors. Take a client portfolio, imagine alternative 10-year market histories, report the distribution of outcomes against the client's goals.

**Institutional API.** High-throughput stress testing for quant research teams. Batch submit 100+ strategies, get back a distribution of overfitting percentiles, sort and rank. Integrates with enterprise research workflows.

**Other verticals.** Supply chain demand forecasting, insurance pricing, energy grid optimization. Each vertical swaps out the Market Imaginer for a domain-specific generator and reuses the rest of the pipeline.

## Why this order

Phases are ordered by two principles: each phase stands alone as a shippable product, and each phase is an additive build on the previous phase rather than a rewrite.

- **v1 ships the core insight** in the minimum viable form. One user flow, one tab pair, one generator. If v1 is wrong, the whole bet is wrong, and we find out before building anything harder.
- **v2 extends the insight across regimes and conditions.** Arena and Regimes are natural extensions of Forge. Live is the visually impressive one that makes the product feel alive. v2 is the phase where we go from "technically impressive" to "obviously valuable."
- **v3 monetizes.** We do not add accounts and billing until we know users want the product. Launching Phase 3 without demand would burn engineering on infrastructure instead of on the insight.
- **v4 generalizes.** The platform play is only sensible after the trading wedge has real users. Premature generalization destroys category clarity and confuses customers.

## Deprecations and known sunsets

**The GBM primary generator.** When Kronos becomes primary in v2, GBM drops to fallback-only status. It stays in the repo because it is the fastest way to run tests without model weights, but it is no longer the default user-facing generator.

**Stub audio narration.** The pre-recorded VibeVoice stubs are a v1 optimization. They are deleted in v2 when live synthesis replaces them.

**The 200-scenario default.** As Kronos inference gets faster, we expect to raise this to 500 or 1,000 without blowing the latency budget. The number is a parameter, not a structural constant.

## Technical debt carried into v2

Known items we will fix in v2 rather than v1 because the v1 scope is tight:

- **Strategy code sandbox hardening.** v1 uses multiprocessing subprocess + 5-second timeout. v2 should add resource limits (CPU time, memory, file descriptors) via `resource.setrlimit` in the subprocess, and should consider wasm-based isolation for the strategy execution path.
- **Fan chart scaling.** v1 renders 20 sample ghost lines + percentile bands. If we raise scenario count to 500+ in v2, we may need to switch from Recharts ComposedChart to a canvas-based renderer for performance.
- **Kronos context pinning.** v1 uses a fixed 2023-H1 window for SPY real data. v2 should let the user pick the real-backtest window and should cache Kronos model weights per window.
- **Anthropic rate limiting.** v1 does not retry Anthropic calls on rate-limit errors. v2 should add exponential backoff with jitter.

## What success looks like per phase

**v1 success:** 10 real users run 100+ stress tests in the first month. The fan chart is shared on at least one social media channel. At least one user reports that QuantForge stopped them from deploying an overfit strategy.

**v2 success:** 500 real users. Regimes tab is the most-used tab after Forge. Live tab is the most-screenshotted tab. Kronos-generated fan charts are visibly more realistic than GBM-generated ones and users notice.

**v3 success:** 50 paying users at $30/month. One $500/month team subscription. One enterprise conversation in flight.

**v4 success:** The first non-trading vertical ships (risk manager for wealth advisors). QuantForge is cited in a research paper about distributional stress testing as a general technique.
