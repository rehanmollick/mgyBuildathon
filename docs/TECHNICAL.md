# TECHNICAL

A deep dive on each agent, the math behind the metrics, and the reasoning behind every non-obvious choice in the pipeline.

## Agent 1: Strategy Architect

### Input

A plain-English description of a trading strategy. Examples:

- *"Buy when the 50-day moving average crosses above the 200-day, sell on the cross below, 3% stop loss."*
- *"Mean reversion: buy when RSI drops below 30, sell when it crosses above 70."*
- *"Momentum: buy on three consecutive green candles, sell after two red candles."*

### Processing

The agent sends the description to Claude with a system prompt that enforces:

1. Output is a single Python function with the exact signature `def strategy(df: pd.DataFrame) -> pd.Series`.
2. The input DataFrame has columns `open`, `high`, `low`, `close`, `volume` with a `DatetimeIndex`.
3. The returned Series has the same index as the input and values in `{-1, 0, 1}` meaning sell, hold, buy.
4. Only pandas, numpy, and the standard library are allowed. All technical indicators are implemented from scratch.
5. The function must not have side effects, network calls, or file I/O.
6. The function must handle NaN values and avoid lookahead bias (never using future data to decide past signals).

### Output validation

The returned code is parsed into an AST and checked:

- Exactly one top-level function definition named `strategy`.
- The function has exactly one parameter named `df`.
- No `import` statements other than `pandas`, `numpy`, and the standard library.
- No calls to network, filesystem, or subprocess APIs.
- The body must not contain `while True` or unbounded recursion (we rely on `safe_exec`'s subprocess timeout as a second line of defense).

Failures raise `StrategyParseError` with the specific reason. The caller receives a structured error and can retry with a clarifying prompt.

### Why Claude and not a DSL

A domain-specific language would remove ambiguity but would also impose a learning curve on every user. Natural language has one huge advantage: everyone already speaks it. Claude at the 4.6 generation is reliable enough to convert English to correct Python for common trading patterns (moving averages, RSI, MACD, Bollinger Bands, momentum, breakout, mean reversion) without hand-holding. The error rate on novel or underspecified descriptions is non-zero, but the parser catches the failures and returns an actionable error.

## Agent 2: Market Imaginer

### The distribution problem

Traditional backtesting tests your strategy against one history: the actual market path from start date to end date. That path is one sample from a distribution of possible market paths that never existed. If your strategy returned 40% on that path, you have no way to know whether the 40% is a robust edge or a lucky draw from a wide distribution.

The Market Imaginer generates N alternative market paths so the Backtester can run the strategy against every one and compute a distribution of outcomes.

### Generator A: Geometric Brownian Motion (primary, v1)

GBM is the workhorse. We calibrate it to the historical volatility of the target asset:

```
log(S_t / S_{t-1}) ~ N(mu, sigma^2)

where:
  mu    = annualized drift estimated from historical log returns
  sigma = annualized volatility estimated from historical log returns
```

Given a starting price `S_0` and a target length `T`, we sample `T` independent log returns and compound them into a price path. Repeat N times to get N paths. For OHLC sampling, we generate the close path via GBM and then construct open/high/low per bar using a simple intracandle model that preserves the empirical relationship between close-to-close returns and intrabar range.

GBM's limitations are well known. It assumes constant volatility, Gaussian returns, and no regime transitions. Real markets have volatility clustering, fat tails, jumps, and structural breaks. But GBM has three advantages that make it the right v1 default:

1. **It is fast.** 200 paths of 126 bars each in well under one second on any hardware.
2. **It is deterministic under a seed.** Tests are reproducible.
3. **It is realistic enough to expose overfitting.** The strategies that curve-fit to noise fail under GBM the same way they fail under more sophisticated generators, because the failure mode (optimizing parameters to one arbitrary path) is not specific to the distributional assumptions of the generator.

### Generator B: Kronos-mini (alternate, v2 primary)

Kronos (Neo Quasar, AAAI 2026) is a decoder-only transformer trained on 12 billion candlesticks from 45 global exchanges. It tokenizes OHLCV sequences as language and generates continuations via autoregressive sampling. Kronos-mini has 4 million parameters and runs on CPU. Kronos-base has 102 million parameters and runs on a modest GPU.

The v1 alternate module `market_imaginer_kronos.py` provides a typed interface over the Kronos API. The correct way to generate N distinct paths is:

```python
predictor.predict_batch(
    df_list=[context_df] * n_scenarios,
    sample_count=1,       # per-input sample count
    T=1.0,                # sampling temperature
    top_p=0.9,            # nucleus sampling
)
```

The subtlety here is that Kronos's `sample_count` parameter averages trajectories before returning rather than giving N individual paths. The correct approach is to pass the same context N times through the batch API, which produces N distinct paths under stochastic sampling in one batched forward pass.

At v1 the Kronos module is unit-tested with mocks. At v2 the module will be the primary generator with GBM as the fallback. The architecture supports either via a shared `Generator` protocol.

### Why not GARCH, Heston, or financial GANs?

- **GARCH** models volatility clustering well but struggles with jumps and regime transitions. The calibration procedure is slower than GBM without being much more realistic than Kronos.
- **Heston** adds stochastic volatility to Black-Scholes. Popular in options pricing, overkill for strategy stress testing where we care about marginal distribution shape more than second-order moments.
- **Financial GANs** are an active research area but most published models mode-collapse or produce unrealistic samples on long horizons. Kronos is the first foundation model with credible open-source weights and is our v2 target.

## Agent 3: Backtester

### Portfolio simulation

For each market path, we run the strategy and maintain a portfolio state machine:

```
position = 0
equity = [1.0]
entry_price = None

for t in range(1, len(prices)):
    signal = signals.iloc[t - 1]  # use yesterday's signal to decide today

    if signal == 1 and position == 0:
        position = 1
        entry_price = prices.iloc[t]
    elif signal == -1 and position == 1:
        position = 0
        trade_return = (prices.iloc[t] - entry_price) / entry_price
        equity.append(equity[-1] * (1 + trade_return))
        continue

    if position == 1:
        unrealized = (prices.iloc[t] - entry_price) / entry_price
        equity.append(equity[-1] * (1 + unrealized))
    else:
        equity.append(equity[-1])
```

The key detail is that we use the signal from `t-1` to decide the trade at `t`. This prevents lookahead bias, where the strategy peeks at the current-bar close to decide the current-bar trade, which would be unexecutable in live trading.

### Metrics

**Total return.** Final equity divided by initial equity, minus one.

**Max drawdown.** The largest peak-to-trough decline in the equity curve.

```python
peak = np.maximum.accumulate(equity)
drawdown = (equity - peak) / peak
max_drawdown = drawdown.min()
```

**Sharpe ratio.** Annualized return divided by annualized volatility of daily returns, assuming zero risk-free rate.

```python
daily_returns = np.diff(equity) / equity[:-1]
sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
```

**Probability of ruin.** Fraction of synthetic paths where equity ever drops below some threshold (we use 0.5, a 50% drawdown, as the "ruin" level). Higher values indicate a strategy that risks catastrophic failure.

**Overfitting percentile.** The key metric. Defined as the percentile rank of the real-history total return within the distribution of synthetic-history total returns. Computed via `scipy.stats.percentileofscore`. Higher values mean the real result is an outlier in the distribution.

### The overfitting percentile math

Given:
- `real_return`: total return on real historical data
- `synthetic_returns`: list of total returns from N synthetic paths

We compute:

```python
from scipy.stats import percentileofscore

overfitting_percentile = percentileofscore(synthetic_returns, real_return, kind="mean")
```

Interpretation:
- **50th percentile**: real result is typical, strategy is not overfit.
- **90th percentile**: real result is better than 90% of synthetic outcomes, suggesting the real history was favorable to the strategy's specific parameters.
- **97th percentile or higher**: real result is a significant outlier, strongly suggesting overfitting to the one historical path.

This is more meaningful than the z-score-based formula (`abs(z) * 25`) originally considered, because it does not assume a normal distribution of synthetic returns. Real synthetic distributions from GBM or Kronos are skewed and fat-tailed, and a percentile is distribution-free.

### safe_exec

User-provided strategy code runs in a multiprocessing subprocess with a timeout:

```python
def safe_exec(code: str, df: pd.DataFrame, timeout: float = 5.0) -> pd.Series:
    ctx = multiprocessing.get_context("spawn")
    q: multiprocessing.Queue = ctx.Queue()
    p = ctx.Process(target=_run_strategy_in_subprocess, args=(code, df, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        raise StrategyTimeout(f"Strategy exceeded {timeout}s timeout")
    if not q.empty():
        result = q.get()
        if isinstance(result, Exception):
            raise StrategyExecutionError(str(result))
        return result
    raise StrategyExecutionError("Subprocess produced no result")
```

The `spawn` context avoids fork-related issues on macOS and ensures a clean Python interpreter for each run. The subprocess communicates results via a `multiprocessing.Queue`, and exceptions inside the subprocess are wrapped into the queue and re-raised in the parent.

We intentionally do not use `signal.alarm`. Signals only fire on the main thread, and uvicorn request handlers do not run on the main thread. A signal-based timeout would silently fail in production.

## Agent 4: Analyst

The Analyst takes a `BacktestResult` pydantic model and writes a three-to-four-sentence verdict. The system prompt instructs Claude to:

1. State the real-history total return as a percentage.
2. Compare it to the median synthetic return to contextualize.
3. State the overfitting percentile and explain its meaning.
4. State the probability of ruin if it is above 15%.
5. End with a one-sentence judgment: robust edge, moderate overfitting concern, or likely overfit.

The output is deterministic under seed (temperature 0.3) and strictly numerical. We grind on the prompt until Claude never hallucinates numbers that are not in the metrics.

## Agent 5: Narrator

The Narrator returns a URL to an audio file. In v1, it returns a pre-recorded stub keyed by preset strategy ID. In v2, it synthesizes fresh audio with VibeVoice-1.5B.

VibeVoice-1.5B (Tencent, ICLR 2026, MIT license) is a text-to-speech model trained on multispeaker audiobook data. It supports emotional tone control and produces audio that sounds like a confident analyst rather than a robotic dictation. The v2 pipeline runs VibeVoice on a GPU cache-warmed at server boot. The synthesized audio is cached per verdict text hash so repeated verdicts return instantly.

The `/api/narrate` endpoint is intentionally separate from `/api/forge`. The frontend fires both in parallel: `/api/forge` returns chart data within ~15 seconds, and `/api/narrate` returns an audio URL within ~2 seconds (stub) or ~8 seconds (live VibeVoice). The audio finishes loading during the chart reveal animation, so the user experiences them as simultaneous without the backend having to serialize them.

## Agent 6: Strategy Mutator

The Mutator takes a baseline strategy and asks Claude for ten variants. The system prompt structures the variants across four axes:

1. **Parameter changes.** Different moving-average windows, different RSI thresholds, different stop-loss levels.
2. **Filter additions.** Volume confirmation, trend filter, volatility regime filter.
3. **Indicator combinations.** Add MACD to an RSI strategy, add Bollinger Bands to a moving-average strategy.
4. **Risk management changes.** Different position sizing, trailing stops, time-based exits.

The response is a list of `{ description, code }` objects. Each variant is validated the same way Agent 1's output is validated. Variants that fail validation are dropped and Claude is re-prompted for replacements.

Critically, all ten variants are backtested against the *same* 200 synthetic markets that the baseline strategy was tested against. Markets are strategy-agnostic, so Agent 2 is called once per Evolve run, not eleven times. This is what makes Evolve cheap.

## Orchestration and concurrency

Agents are composed in the orchestrator as `await` calls. The Backtester is sync (CPU-bound) and is offloaded to a thread via `asyncio.to_thread` so the event loop stays free for other incoming requests.

Per-variant timeouts in the Evolve flow are enforced via `asyncio.wait_for`. If a single variant hangs (rare, but possible if Claude generates a poorly-bounded loop), the variant is killed at 4 seconds and the other variants continue. The Evolve endpoint also has a total wall-clock cap of 45 seconds enforced at the FastAPI layer.

## Observability

Every agent logs entry and exit via structlog with a request ID threaded through from the FastAPI middleware. Logs are JSON, so they can be grepped, piped to a log collector, or turned into metrics. Example:

```json
{
  "event": "agent.start",
  "agent": "market_imaginer",
  "request_id": "req_7f3a...",
  "asset": "SPY",
  "n_scenarios": 200,
  "generator": "gbm",
  "timestamp": "2026-04-11T16:45:22Z"
}
```

The `/api/health` endpoint returns a structured health status with per-dependency checks: Anthropic API reachability, Kronos weights presence (if configured), historical market data availability.
