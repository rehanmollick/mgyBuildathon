/**
 * Pre-computed demo fixtures. The frontend falls back to these when the
 * backend is unreachable, so the demo mode works with zero network.
 */

import type { BacktestResult, ForgeResult, EvolveResult } from "./types";

const buildEquityCurve = (length: number, drift: number, seed: number): number[] => {
  let s = seed;
  const rand = (): number => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
  const out: number[] = [1.0];
  for (let i = 1; i < length; i++) {
    const shock = (rand() - 0.5) * 0.02;
    const last = out[i - 1]!;
    out.push(last * (1 + drift + shock));
  }
  return out;
};

const buildDates = (length: number): string[] => {
  const start = new Date("2023-07-01");
  const out: string[] = [];
  for (let i = 0; i < length; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    out.push(d.toISOString().slice(0, 10));
  }
  return out;
};

const N_STEPS = 120;
const N_SCENARIOS = 80;

const buildDemoResult = (drift: number, seed: number): BacktestResult => {
  const real_curve = buildEquityCurve(N_STEPS, drift, seed);
  const synth_curves = Array.from({ length: N_SCENARIOS }, (_, i) =>
    buildEquityCurve(N_STEPS, drift * 0.5, seed + i + 1),
  );

  const sorted_at = (t: number): number[] =>
    [...synth_curves.map((c) => c[t]!)].sort((a, b) => a - b);

  const p05: number[] = [];
  const p50: number[] = [];
  const p95: number[] = [];
  for (let t = 0; t < N_STEPS; t++) {
    const col = sorted_at(t);
    p05.push(col[Math.floor(col.length * 0.05)]!);
    p50.push(col[Math.floor(col.length * 0.5)]!);
    p95.push(col[Math.floor(col.length * 0.95)]!);
  }

  const total_returns = synth_curves.map((c) => c[c.length - 1]! - 1);
  const max_drawdowns = synth_curves.map((c) => {
    let peak = c[0]!;
    let worst = 0;
    for (const v of c) {
      if (v > peak) peak = v;
      const dd = (v - peak) / peak;
      if (dd < worst) worst = dd;
    }
    return worst;
  });
  const sharpes = synth_curves.map((curve) => {
    const rets: number[] = [];
    for (let i = 1; i < curve.length; i++) {
      rets.push(curve[i]! / curve[i - 1]! - 1);
    }
    const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
    const variance = rets.reduce((a, b) => a + (b - mean) ** 2, 0) / rets.length;
    const std = Math.sqrt(variance);
    return std === 0 ? 0 : (mean / std) * Math.sqrt(252);
  });
  const ghost_lines = synth_curves.slice(0, 20);

  return {
    real: {
      total_return: real_curve[real_curve.length - 1]! - 1,
      max_drawdown: -0.14,
      sharpe: 1.62,
      equity_curve: real_curve,
    },
    synthetic: {
      total_return_distribution: total_returns,
      max_drawdown_distribution: max_drawdowns,
      sharpe_distribution: sharpes,
      percentile_bands: {
        timestamps: buildDates(N_STEPS),
        p05,
        p50,
        p95,
      },
      ghost_lines,
    },
    probability_of_ruin: 0.12,
    overfitting_percentile: 78.4,
  };
};

export const DEMO_FORGE_RESULT: ForgeResult = {
  request_id: "req_demo_forge",
  code: `import pandas as pd
import numpy as np

def strategy(df: pd.DataFrame) -> pd.Series:
    close = df["close"]
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    signals = pd.Series(0, index=df.index)
    signals[ma50 > ma200] = 1
    signals[ma50 < ma200] = -1
    return signals
`,
  summary:
    "Your strategy performed at the 78th percentile of synthetic markets — better than most, but suggestive of mild overfit.",
  result: buildDemoResult(0.002, 99),
  verdict:
    "Your strategy returned a healthy number on the real market, but it only beat three quarters of the synthetic alternatives. A genuinely robust strategy would land near the median. The result is not alarming, but watch the drawdown distribution — the tail risk is larger than the headline return suggests.",
};

export const DEMO_EVOLVE_RESULT: EvolveResult = {
  request_id: "req_demo_evolve",
  baseline: {
    rank: 0,
    description: "Buy when RSI < 30, sell when RSI > 70",
    code: "def strategy(df):\n    return pd.Series(0, index=df.index)",
    result: buildDemoResult(0.001, 42),
    overfitting_percentile: 88.2,
  },
  variants: [
    {
      rank: 1,
      description: "RSI(14) with 20-day volume filter",
      code: "def strategy(df):\n    return pd.Series(0, index=df.index)",
      result: buildDemoResult(0.0008, 43),
      overfitting_percentile: 52.1,
    },
    {
      rank: 2,
      description: "RSI(10) with tighter thresholds (25/75)",
      code: "def strategy(df):\n    return pd.Series(0, index=df.index)",
      result: buildDemoResult(0.0012, 44),
      overfitting_percentile: 61.7,
    },
    {
      rank: 3,
      description: "RSI(14) combined with 50-day trend filter",
      code: "def strategy(df):\n    return pd.Series(0, index=df.index)",
      result: buildDemoResult(0.0007, 45),
      overfitting_percentile: 65.2,
    },
  ],
  verdict:
    "The most robust variant adds a 20-day volume filter to the RSI trigger. It gives up ~10% on real-market return but lands near the median of synthetic performance, which is what robustness looks like.",
};
