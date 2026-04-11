# USER STORIES

Four personas. Each has a background, a goal, a flow through QuantForge, and a specific outcome that changes what they do next.

## Persona 1: Mia, retail algo trader (primary)

**Background.** Mia is 28, works as a data engineer at a mid-size SaaS company, and trades her own money on the side. She has about $35k in a taxable brokerage account and runs one momentum strategy on BTC and one mean-reversion strategy on QQQ. She learned Python from work, reads r/algotrading and Ernest Chan books on weekends, and is good enough to write her own strategies but not good enough to know when her own strategies are lying to her.

**Goal.** She built a new strategy last weekend: "Buy QQQ when RSI drops below 25 and the 5-day moving average is above the 20-day moving average, sell when RSI crosses above 65." Her Backtrader results show 52% annualized returns over the last five years with a 14% max drawdown. She is excited. She is also suspicious, because the last three strategies that looked this good in backtesting lost her money in live trading. She wants a second opinion.

**Flow.**
1. Mia opens QuantForge and pastes her strategy description into the Forge text box.
2. She clicks Forge. The ProgressSteps indicator animates through Parse → Imagine → Test → Analyze.
3. Within fifteen seconds, the dashboard populates. The fan chart shows her green real-history equity curve floating above a translucent cloud of synthetic equity curves. Most of the cloud is below zero.
4. She looks at the overfitting percentile gauge. It reads 94th percentile. Red.
5. She reads the verdict: *"Your strategy returned 52% on real QQQ data, but in 781 out of 1,000 alternative histories it lost money. Your real-history result sits at the 94th percentile of synthetic outcomes, meaning your backtest looks like an outlier rather than a reliable edge. The 22% probability of ruin under synthetic stress suggests the strategy depends heavily on one specific regime and is not robust."*
6. Mia clicks the Evolve tab, pastes the same strategy, and hits Evolve. The Mutator generates ten variants. She scrolls the leaderboard. One variant with a 20-day MA instead of 5-day and RSI thresholds of 30/70 instead of 25/65 shows an overfitting percentile of 58 — still slightly elevated but much more robust.
7. Mia deploys the robust variant with a smaller position size, knowing the edge is real but modest.

**Outcome.** Mia did not deploy the 52%-annualized strategy that would have lost her money. She deployed a 22%-annualized variant that actually holds up in alternative histories. QuantForge saved her the six weeks of pain it would have taken to discover the same thing in production.

## Persona 2: David, quant research analyst at a systematic hedge fund

**Background.** David is 34, PhD in statistical physics, works at a $2B systematic fund in the momentum group. His job is to generate and test new factor strategies, and his PM gives him maybe two hours per week per strategy before the idea moves forward or gets killed. Walk-forward analysis on the fund's production system takes six hours per run. David wants a faster initial filter.

**Goal.** He has a list of twelve candidate momentum strategies he thinks are promising. He needs to know which three are worth running through the full walk-forward pipeline. He does not want to waste compute on the nine that will fail the walk-forward test anyway.

**Flow.**
1. David posts each candidate strategy to QuantForge as a batch overnight via the API.
2. The next morning he pulls the JSON responses and sorts by overfitting percentile.
3. Nine strategies have overfitting percentiles above 85. He eliminates them without further testing.
4. Three strategies have overfitting percentiles between 55 and 70. He runs those through the fund's full walk-forward pipeline.
5. Two of the three pass walk-forward. David presents them to his PM.

**Outcome.** David saved twelve hours of walk-forward compute on strategies that would not have passed. His PM approves one of the two survivors. David's batting average (strategies proposed versus strategies deployed) goes from 1 in 15 to 1 in 3. At his next review, he asks for a raise.

## Persona 3: Professor Elena, finance educator

**Background.** Elena teaches an applied quantitative finance course at a mid-tier business school. Her students are MBAs who need to understand overfitting and survivorship bias as concepts but who do not have the quant background to derive the math from scratch. Her current teaching tool is a Jupyter notebook that runs a simple Monte Carlo simulation. The students find it confusing.

**Goal.** Elena wants a live, interactive demonstration of overfitting for her next lecture. She wants to show her students a strategy that looks great in backtesting, click a button, and reveal that it falls apart in alternative histories. She wants the reveal to be visual and visceral, not statistical and abstract.

**Flow.**
1. Elena projects QuantForge on the lecture hall screen.
2. She pastes in a deliberately overfit strategy: "Buy when the 50-day MA crosses above the 200-day MA, sell on the cross below, 3% stop loss, but only in January through March." The time-filter is the overfitting trap, because it was tuned to one good quarter.
3. She clicks Forge. The fan chart builds.
4. The real equity curve is a beautiful smooth green line going up 45%. The cloud of synthetic equity curves is a mess, with 70% of paths below zero.
5. The students gasp. The overfitting percentile reads 91.
6. Elena reads the verdict aloud: *"Your strategy returned 45% on real SPY data, but in 701 out of 1,000 alternative histories it lost money..."*
7. She opens the Evolve tab and shows students how removing the time filter produces variants with much lower overfitting percentiles.
8. The students never forget what overfitting feels like.

**Outcome.** Elena's course evaluations improve. Three students ask whether they can use QuantForge for their final project. One student uses it to stress-test their own personal portfolio strategy and finds it's overfit. They tell their friends.

## Persona 4: Alex, founder of a fintech that offers an execution platform

**Background.** Alex runs a two-year-old fintech that sells an execution platform to retail algo traders. Users connect a brokerage account, write strategies in the platform's web IDE, and Alex's platform routes orders. Alex's retention is good for users who make money and terrible for users who don't. The users who don't make money all have the same story: their strategies looked great in backtesting and failed in production. Alex wants to reduce the number of users who deploy overfit strategies.

**Goal.** Alex wants to add a "stress test" button to his platform's strategy editor that runs the user's strategy against 200 synthetic market histories and warns them if the overfitting percentile is above 80. He does not want to build the stress-testing engine himself. He wants to integrate with an API.

**Flow.**
1. Alex evaluates QuantForge's API (`/api/forge` and `/api/evolve`).
2. He signs up for a team tier at $500/month and gets API credentials.
3. His engineering team adds a "Stress Test" button to the strategy editor that posts the user's strategy code directly to the QuantForge API.
4. When the overfitting percentile exceeds 80, a warning banner appears in the editor with the Analyst's verdict text.
5. Users who ignore the warning and deploy anyway see the warning again in their deployment history dashboard.

**Outcome.** Alex's retention improves by 15% over two quarters because users who would have lost money now delete their overfit strategies instead. Alex integrates QuantForge deeper, adding the Evolve flow as a "Robustness Check" feature. He signs a two-year contract at $24k/year with volume-based overage.

## What these four personas share

- **They all trust statistical distributions more than point estimates.** The insight "one number is not enough" is the core pitch.
- **They all learned about overfitting the hard way.** The product resonates because it addresses a pain they already feel.
- **They all need speed.** Fifteen seconds per stress test is the difference between "I'll use this on every strategy" and "I'll use this on some strategies when I remember."
- **They all value the fan chart.** The visual is the product. Remove it and the product is a JSON response.

## What the four personas do not share

- **Price sensitivity.** Mia will pay $30/month, grudgingly. David's fund will pay $25k/year without asking. Elena wants free. Alex wants per-API-call pricing. v1 is free tier only. v2 adds paid tiers keyed to these distinct willingness-to-pay profiles.
- **Technical depth.** Mia writes Python. David writes Rust. Elena reads Python and writes LaTeX. Alex reads pull requests. The API surface needs to be approachable for Mia and complete enough for Alex.
- **Volume.** Mia runs one strategy. David runs twelve. Alex runs thousands on behalf of his users. The backend is built stateless and horizontally scalable so volume is not a cliff.

These four personas define the product edges. Everything in v1 is designed so all four can walk away from a first session with a moment that made them trust the tool.
