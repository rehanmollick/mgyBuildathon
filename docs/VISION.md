# VISION

**One sentence:** QuantForge turns plain-English trading strategies into a distribution of possible outcomes, so traders can see whether their edge is real or whether they got lucky in the one history that happened.

## The thesis

Every trading strategy ever shipped was validated against one history, the one that actually occurred. That history is a single sample from a distribution of market paths that never existed. The strategy that returned 40% last year might have lost money in 873 out of 1,000 equally plausible alternative histories. Traditional backtesting cannot show you that, because traditional backtesting only has one history to test against.

QuantForge generates the distribution. A six-agent AI pipeline converts an English description into executable Python, imagines two hundred synthetic market histories using generative market models, runs the strategy against every one of them, and returns one number that answers the question every quant is afraid to ask: *is my strategy actually good, or did I get lucky?*

## The product

QuantForge v1 ships two flows:

1. **Forge** — the stress-test loop. User types "Buy when the 50-day moving average crosses above the 200-day, sell on the cross below." QuantForge parses it, generates 200 alternative market histories, runs the strategy against every one, and returns a fan chart of equity curves, distributions of returns and drawdowns and Sharpe ratios, a probability-of-ruin gauge, and an overfitting percentile that says where the real-history result falls in the distribution of synthetic outcomes. A Claude-written verdict narrates the meaning in plain English. An optional voice layer reads it aloud.

2. **Evolve** — the mutation search. User takes a baseline strategy, clicks Evolve, and Claude generates ten parametric variants. Every variant runs through the same 200 markets, and the user gets a ranked leaderboard sorted by overfitting percentile. The robust variants float to the top. The brittle variants sink. The user learns which parameter choices were actually load-bearing versus which were curve-fitted to a single path.

v2 adds Arena (head-to-head strategies), Regimes (stress testing conditioned on market regime), and Live (real-time Binance feed with on-the-fly prediction bands). See [ROADMAP.md](./ROADMAP.md).

## Why now

Three things changed in 2025-2026 that made QuantForge possible:

- **Foundation models for financial time series.** Kronos (MIT license, AAAI 2026, 102M params) is a generative transformer trained on 12 billion candlesticks from 45 global exchanges. For the first time, you can sample synthetic market histories that exhibit real volatility clustering, realistic intracandle range, and believable regime transitions, rather than the smooth Brownian nonsense Monte Carlo has been producing for thirty years. Kronos is the alternate generator in v1 and the primary in v2 once weights are provisioned. Geometric Brownian Motion, calibrated to real volatility, is v1's primary generator because it is fast, deterministic, and deployable without a GPU, while still producing distributions rich enough to expose overfitting.
- **LLMs that write correct Python.** Claude can reliably convert a natural-language strategy description into a typed Python function with the right signature, the right indicator math, and the right edge-case handling. Five years ago this would have required a domain-specific language. Today it is one Claude call with a strict system prompt.
- **Cheap cloud compute.** Generating 200 synthetic markets and running 200 backtests takes under fifteen seconds on consumer hardware. Ten years ago this was a weekend-long batch job on a research cluster. Today it is a real-time feedback loop.

Put them together and you get a product that was not possible before and is obvious in hindsight.

## The market

The global algorithmic trading market was estimated at $21 billion in 2025 and projected to reach $42 billion by 2033. Within that, the addressable wedge for pre-trade strategy validation is the intersection of:

- **Retail algo traders** on platforms like QuantConnect, TradingView, and Interactive Brokers. Roughly 15 million active accounts globally with some level of custom strategy development. Even a 1% conversion into a $30/month tool is a $54M ARR business.
- **Quant research teams at hedge funds and prop shops.** Smaller volume, much higher willingness to pay. A team-tier product at $10k/year per seat and 500 seats is $5M ARR.
- **Finance educators** teaching quantitative methods. Universities and online course platforms that want a visual, interactive tool for teaching overfitting, survivorship bias, and walk-forward analysis. Low revenue, high brand value.
- **Fintech platforms** that want to add strategy validation as a feature without building it themselves. API-first tier, usage-based pricing.

The core insight is that every trader builds strategies that look great in backtesting and then quietly underperform in production. The gap between paper alpha and real alpha is exactly what QuantForge measures. Selling a measurement of regret is a durable business.

## The long-term bet

QuantForge is a wedge into a larger category: the stress-testing layer for any AI or algorithmic system that makes decisions against uncertain futures. Trading is the first vertical because the signal is clean and the feedback loop is fast, but the same primitives (generate alternative histories, run the system, measure dispersion) apply to:

- Portfolio risk management for wealth advisors
- Supply chain decision systems (alternative demand trajectories)
- Energy trading and grid optimization
- Insurance pricing models
- Any reinforcement learning policy that needs off-policy evaluation under distribution shift

The six-agent architecture is general. Replace Agent 2 (Market Imaginer) with a different generator and QuantForge becomes a generic distributional stress-testing platform. The trading product is the wedge. The platform is the long game.

## Why we win

Three defensible moats:

- **Architecture clarity.** Six named agents with typed contracts and a 30-line orchestrator is easier to extend, reason about, and trust than a monolithic CRUD app with a pile of endpoints. Teams that understand their own architecture ship faster.
- **Model composition.** We are not a wrapper around one model. We compose Claude (twice) with Kronos/GBM and VibeVoice in a pipeline where each model does exactly what it is best at. Swapping any component is one module change, not a rewrite.
- **Narrative legibility.** The product makes an intuitive metaphor concrete: a clean green equity curve drowning in a cloud of ghost histories. That image sells the product without words. It is the kind of visual that spreads on social media and makes a category.

## What QuantForge is not

- Not a trading bot. We do not execute orders. We stress-test the strategies you execute elsewhere.
- Not a broker. We connect to market data, not order flow.
- Not a forecasting tool. We do not predict the future. We simulate plausible alternative pasts to measure how dependent your strategy was on the one past that happened.
- Not a replacement for walk-forward analysis. We are faster, cheaper, and complementary.

## Success in 12 months

- 5,000 free-tier users running at least one stress test per month
- 150 paid-tier users at $30/month
- One published case study of a strategy that looked great in backtesting, failed the QuantForge overfitting test, and subsequently failed in live trading
- Integration with at least one retail broker platform
- v2 shipped (Arena, Regimes, Live)
- Series A raised on the back of real usage data

## Success in 36 months

- 100,000 users, 5,000 paid
- Enterprise tier shipping into quant funds
- Generalization beyond trading into one adjacent vertical (insurance pricing or supply chain)
- Kronos fine-tunes for specific asset classes (equities, FX, commodities, crypto)
- The phrase *"I QuantForged my strategy"* appears in trader slang
