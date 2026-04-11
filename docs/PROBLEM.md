# PROBLEM

## The user's pain

A retail algo trader spends two weeks writing a moving-average crossover strategy. They backtest it on ten years of SPY data and it returns 40% annualized with a 12% max drawdown and a Sharpe of 1.8. The equity curve is smooth. Every metric looks good. They deploy it with real money.

Six weeks later they are down 18%. The strategy is still trading. The code is unchanged. What happened?

What happened is that the ten-year history was a single sample from a distribution of possible histories, and their strategy had quietly curve-fitted to noise in that specific sample. The 50-day and 200-day window lengths were not chosen from first principles. They were chosen because 49-day and 201-day happened to return slightly less on that exact historical path. The 3% stop loss was picked because 2.5% and 3.5% had worse Sharpe ratios on that exact history. Every decision in the strategy was optimized for one arbitrary draw from an unseen distribution, and when the distribution rolled again, the arbitrary choices became liabilities.

This is overfitting. It is the single biggest reason retail algo traders lose money, and it is invisible in every tool they use.

## Why it is invisible

Traditional backtesting has a structural flaw: it can only test one history. The history that happened. If your strategy returned 40% in that history, the backtester tells you 40%. It cannot tell you that the 40% is a lucky draw from a distribution where the 50th percentile was 4%.

Walk-forward analysis is better. It splits the history into training and validation windows and refits the strategy on each window. It catches some overfitting because it tests whether the strategy generalizes to *held-out segments* of the same history. But walk-forward analysis still only tests against one history. It cannot answer the question: *if the last ten years had unfolded differently, would this strategy still work?*

Cross-validation does not help, because market time series are not independent samples. You cannot shuffle candles and reason about a strategy's performance. The temporal structure matters and cross-validation breaks it.

Monte Carlo simulation is an attempt to generate alternative histories, but it uses simple statistical models (geometric Brownian motion with constant volatility, or GARCH with a handful of parameters) that produce histories looking nothing like real markets. The synthetic histories have no volatility clustering, no fat tails, no regime transitions, no realistic intracandle structure. A strategy that looks great on Monte Carlo often fails on real data because the synthetic data was too smooth to contain the edge cases that real markets produce.

The tool that retail algo traders actually need would generate alternative histories that *look like real markets* and test the strategy against all of them. Until 2025, this tool did not exist because nobody had a model that could generate realistic synthetic financial time series.

## Real examples of invisible overfitting

**The Long-Term Capital Management collapse (1998).** LTCM's convergence trades were backtested over decades of bond market history and showed consistent profits with tiny drawdowns. When Russia defaulted in August 1998, the correlations their models assumed broke down, and the strategies lost $4.6 billion in a few weeks. The backtest had told them the strategies were safe because the one history they tested against did not contain the correlation breakdown. A stress test against synthetic histories with regime transitions would have exposed the fragility.

**The August 2007 quant crisis.** Several large quant hedge funds using similar factor strategies (value, momentum, mean reversion) all experienced simultaneous 20-30% drawdowns over three days. Each fund had backtested its strategies in isolation and found them robust. What they had missed was that other funds were running similar strategies, and when one fund deleveraged, it triggered deleveraging at the others. The backtests were over-optimistic because they tested each strategy in isolation against a history where the crowded-trade dynamic had not yet happened.

**Every retail algo trader who ever posted an equity curve on Reddit showing 300% annualized returns and then went quiet.** The pattern repeats monthly. A trader finds parameters that make their strategy look incredible on historical BTC data. They deploy it, the market regime shifts, and the parameters that worked on 2021 data fail on 2022 data. Nobody in the trader's tool chain told them that their parameters were overfit to the 2021 regime specifically. They had no way to test against alternative regimes because their tool could only replay history.

## Why current solutions fall short

**QuantConnect, TradingView, Backtrader, Zipline.** These platforms do backtesting well and some do walk-forward analysis. None of them stress-test against generatively sampled alternative histories. The user can see their strategy's performance on historical data. They cannot see the distribution it was drawn from.

**Walk-forward analysis implementations.** Technically sound but slow. A proper walk-forward on ten years of data with monthly refits is hours of compute. It produces a single out-of-sample equity curve, not a distribution. The user still has one sample to reason about, just a slightly better one.

**Monte Carlo backtesting tools.** Exist. Most use constant-volatility GBM or GARCH. The synthetic histories are smoother than real markets and miss the regime structure that matters most. Users often dismiss the results because the synthetic data does not look like real data.

**Bootstrap resampling of returns.** Preserves the empirical return distribution but destroys the temporal dependence. Strategies that depend on trends or momentum (most of them) cannot be sensibly tested this way.

**Synthetic data from financial GANs.** Early research. Most models collapse mode or produce unrealistic samples. The field is not yet production-ready. Kronos is the first model with credible public benchmarks.

## What is different now

Three technical shifts in 2025-2026 made the QuantForge approach possible:

1. **Kronos** (Neo Quasar, AAAI 2026) is a decoder-only transformer trained on 12 billion candlesticks from 45 global exchanges spanning equities, FX, commodities, and crypto. It tokenizes OHLCV sequences as language and generates continuations via autoregressive sampling with temperature control. The paper shows that samples preserve volatility clustering, realistic intracandle range, fat tails, and believable regime transitions. For the first time, synthetic financial histories are close enough to real histories that a strategy tested against them gives you actionable information.

2. **Inference costs collapsed.** Kronos-mini (4M parameters) runs on consumer CPUs. Kronos-base (102M parameters) runs in milliseconds per sample on a single H100. Generating 200 synthetic histories for a single stress test costs a few cents and takes about ten seconds. The unit economics of "stress-test on demand" finally work.

3. **LLMs write correct quantitative code.** Claude can convert a trader's English description into a typed Python function with correct indicator math, handling of NaN and lookahead, and reasonable default parameters. This was not possible at Claude 2.1. At Claude 4.6 it is reliable enough to be the first agent in a production pipeline. We do not need a DSL. The natural language is the interface.

## Why QuantForge now

The technical shifts are necessary but not sufficient. The sufficient condition is that somebody compose them into a product with a clear narrative. That is the opportunity.

QuantForge is the first product to compose a natural-language-to-code LLM, a generative financial foundation model, and a plain-compute backtesting engine into a single stress-testing pipeline with a dashboard a retail trader can understand. The architecture is six specialized agents. The interface is a text box and a Forge button. The output is a fan chart that makes overfitting visible for the first time.

The product ships the insight: every backtest is a lie because it tests one history, and QuantForge tests a thousand histories that could have happened. That sentence fits on a T-shirt. The fan chart fits on a Tweet. The category is ready.
