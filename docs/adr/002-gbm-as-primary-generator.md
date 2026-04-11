# ADR 002: GBM as the primary market generator in v1

**Status:** Accepted
**Date:** 2026-04-11
**Deciders:** Rehan Mollick

## Context

The Market Imaginer agent generates synthetic market histories — OHLCV DataFrames that the Backtester runs the user's strategy against. The quality of the synthetic markets determines the quality of the overfitting signal. If the synthetic distributions are wildly unrealistic, a strategy that "works" on them tells us nothing.

Two candidate generators:

**Option A: Kronos.** A 102M-parameter transformer trained on 12 billion OHLCV bars from 45 exchanges (AAAI 2026, NeoQuasar). It tokenizes K-lines as language and generates autoregressively. Trained on real market data, so its outputs reflect learned market structure: fat-tailed returns, volatility clustering, regime shifts, leverage effects.

**Option B: Geometric Brownian Motion (GBM).** A 200-year-old mathematical model of asset prices: log-returns are IID Gaussian with drift μ and volatility σ. Five lines of numpy. Deterministic under a seed. Calibrates instantly from historical data.

Kronos is strictly the better model. It captures real market phenomena GBM cannot. So why would we use GBM as the primary?

## Decision

We use **GBM as the primary market generator in v1**. Kronos is shipped as an alternate module (`market_imaginer_kronos.py`) that can be selected via a config flag but is not exercised in CI or default deployments.

The typed interface (`Generator` protocol) is identical for both:

```python
def imagine(asset: str, n_scenarios: int, seed: int | None = None) -> MarketSet: ...
```

`MarketSet` is a typed object containing N OHLCV DataFrames plus metadata. Either generator can produce it. Swapping is an import change.

## Rationale

### The operational cost of Kronos in v1 is catastrophic

Kronos-base weights are ~500MB. Loading the model takes ~15 seconds on a cold start. Generating 200 scenarios of 250 bars each takes ~8-12 seconds on a GPU and ~60+ seconds on CPU. Hosting Kronos means running a GPU (expensive) or accepting that `/api/forge` takes over a minute on CPU (unacceptable).

None of this is a problem in principle. It's a problem *in v1*, where the product is running on a single Colab H100 exposed via ngrok, or on a cheap PaaS with no GPU. The v1 infrastructure simply cannot serve Kronos to a live user in under 30 seconds end-to-end, which is our latency budget for a good demo experience.

GBM generates 200 scenarios of 250 bars in ~200ms. Total pipeline latency with GBM is ~15 seconds (dominated by the two Claude calls, not the generator). The user clicks Forge, the progress bar animates through Parse → Imagine → Test → Analyze, and the dashboard renders before they can get bored. That experience matters.

### GBM is "good enough" for the job it's doing in v1

The Market Imaginer exists to answer one question: *is the strategy's real-market performance typical or anomalous compared to a distribution of plausible alternative histories?*

For that question, the synthetic distribution needs to:
1. Be centered near the real-world return of a buy-and-hold baseline (so the comparison is fair).
2. Have realistic variance (so "typical" and "anomalous" are meaningfully different).
3. Be diverse enough that the overfitting percentile is discriminating (so a well-fit strategy lands at the 50th percentile and an overfit strategy lands at the 95th+).

GBM, calibrated to the empirical volatility of the asset's historical returns, satisfies all three. The distributions are narrower than real markets (GBM has no fat tails, no volatility clustering), but the *ranking* of strategies by overfitting percentile is preserved. A strategy that overfits to the training history will still show up as an outlier in a GBM distribution because GBM's mean reflects the data-generating process GBM was calibrated on, not the idiosyncrasies the strategy memorized.

In other words: GBM is a worse model of markets, but it's sufficient to detect overfitting *for the strategies users actually write*. We validated this by running the pipeline on a dozen known-overfit strategies (curve-fit MA combinations, narrow RSI thresholds) and confirming they all land above the 90th percentile under GBM.

### Kronos's realism is wasted in v1

Kronos's advantage is that its synthetic markets have the *structure* of real markets. For the overfitting percentile, structure doesn't matter much — what matters is variance and diversity. Kronos's structure becomes valuable only for downstream analyses we don't do in v1: regime-conditioned stress tests, tail-risk analysis, volatility surface sensitivity. Those are v2 features.

Shipping Kronos in v1 is paying the full operational cost for benefits that don't materialize until v2. That's backwards.

### The typed interface lets us swap without rewriting

Because `imagine()` has the same signature in both modules, switching to Kronos in v2 is a one-line config change:

```bash
QUANTFORGE_GENERATOR=kronos
```

The orchestrator, the Backtester, the stats module, and the frontend are all unchanged. We get the performance and simplicity of GBM in v1 and the realism of Kronos in v2, without a rewrite.

We also ship the Kronos module *now* (as v1 code, with tests, just not in the default path) so v2 is a deployment change rather than a development change. The Kronos code is typed, tested with mocks, and ready to wire.

### This is an honest tradeoff, and we document it

We are not hiding the Kronos pitch. Every public artifact (README, ARCHITECTURE.md, the Analyst's verdict text) is clear about the v1/v2 split: v1 uses a calibrated GBM generator; v2 swaps in Kronos for real market structure. Users who need Kronos now can set `QUANTFORGE_GENERATOR=kronos` and provide the weights. Users who don't care get the fast path by default.

## Consequences

**Pros:**
- v1 latency target (<30s end-to-end) is easy to hit.
- v1 deploys to any PaaS without GPU requirements.
- The overfitting percentile still works as designed.
- CI runs against GBM (fast, deterministic, reproducible).
- Kronos is shipped as code but not on the default path, so v2 is low-risk.

**Cons:**
- GBM's distributions are thinner than real markets. A strategy that depends on fat-tail behavior (e.g., short volatility strategies) will be under-stressed. We flag this explicitly in the Analyst's verdict text: "This stress test uses a Gaussian market model. Strategies sensitive to tail risk should also be tested against historical drawdown episodes."
- Users expecting Kronos out of the box may be disappointed. Mitigation: the pitch materials are clear about the v1/v2 scope.
- Regime-conditioned stress tests (the Regimes tab) require structure GBM cannot provide, so the Regimes tab is a v2 feature and is not shipped in v1. Rolling Regimes into v2 alongside Kronos is a natural product cut.

## Alternatives considered

**Ship Kronos as primary, accept slow latency.** Rejected: 60+ second latency kills the demo and the pitch experience.

**Ship Kronos as primary on a GPU host.** Rejected: v1 cannot afford a dedicated GPU host. The product must be deployable on a free-tier PaaS.

**Ship GBM only, drop Kronos entirely.** Rejected: Kronos is the v2 story and eventually the product's moat. Cutting it now means rewriting the generator layer in v2. Shipping it as an alternate module costs little and preserves the option.

**Use a simpler bootstrap (historical block resampling).** This generates synthetic markets by resampling contiguous blocks of real returns. It's closer to Kronos in realism than GBM. Rejected because it's not clearly better than GBM for our use case (same ranking behavior) and it introduces a new mode of failure (blocks that end mid-trend create discontinuities). GBM's simplicity wins.

## Revisit criteria

We'll flip the default to Kronos when any of the following are true:

- v2 ships and we have a GPU-backed deployment target (Modal, Replicate, or a persistent GPU instance).
- A user explicitly requests Kronos for fat-tail-sensitive strategies and is willing to tolerate higher latency.
- Kronos inference on CPU becomes fast enough (<10s for 200 scenarios) via quantization or distillation.

Until then, GBM is the default and Kronos is opt-in.
