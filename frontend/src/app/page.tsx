"use client";

import { useState } from "react";

import { ChartCard } from "@/components/ChartCard";
import { CodePreview } from "@/components/CodePreview";
import { EquityCurveFan } from "@/components/EquityCurveFan";
import { Histogram } from "@/components/Histogram";
import { MetricCard } from "@/components/MetricCard";
import { OverfitGauge } from "@/components/OverfitGauge";
import { ProgressSteps, type Step } from "@/components/ProgressSteps";
import { RuinGauge } from "@/components/RuinGauge";
import { StrategyInput } from "@/components/StrategyInput";
import { TabNav } from "@/components/TabNav";
import { VerdictPlayer } from "@/components/VerdictPlayer";
import { forge } from "@/lib/api";
import { colorForReturn, formatNumber, formatPercent, formatSignedPercent } from "@/lib/format";
import type { ForgeResult } from "@/lib/types";

const STEP_SEQUENCE: readonly Step[] = ["parse", "imagine", "test", "analyze"];

export default function ForgePage(): JSX.Element {
  const [result, setResult] = useState<ForgeResult | null>(null);
  const [step, setStep] = useState<Step | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState<boolean>(false);

  const handleSubmit = async (description: string): Promise<void> => {
    setError(null);
    setResult(null);
    setRunning(true);
    const animateSteps = async (): Promise<void> => {
      for (const s of STEP_SEQUENCE) {
        setStep(s);
        await new Promise((resolve) => setTimeout(resolve, 450));
      }
    };
    try {
      const [forged] = await Promise.all([forge({ description }), animateSteps()]);
      setResult(forged);
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setStep(null);
    } finally {
      setRunning(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col">
      <TabNav />
      <div className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-6 pb-16 pt-8">
        <header className="space-y-1">
          <h1 className="text-2xl font-bold text-white">Forge a strategy</h1>
          <p className="text-sm text-muted">
            Describe a strategy in plain English. Claude writes the code, we imagine 200 synthetic
            markets, then we show you whether the backtest was skill or luck.
          </p>
        </header>

        <StrategyInput onSubmit={handleSubmit} disabled={running} />

        {(step !== null || result !== null) && (
          <div className="flex items-center justify-between">
            <ProgressSteps current={step} />
            {error && <span className="text-xs text-loss">{error}</span>}
          </div>
        )}

        {result && (
          <>
            <CodePreview code={result.code} />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
              <MetricCard
                label="Real return"
                value={formatSignedPercent(result.result.real.total_return)}
                tone={result.result.real.total_return >= 0 ? "profit" : "loss"}
              />
              <MetricCard
                label="Max drawdown"
                value={formatSignedPercent(result.result.real.max_drawdown)}
                tone="loss"
              />
              <MetricCard
                label="Sharpe"
                value={formatNumber(result.result.real.sharpe)}
                tone="info"
              />
              <MetricCard
                label="Prob. of ruin"
                value={formatPercent(result.result.probability_of_ruin)}
                tone={result.result.probability_of_ruin > 0.25 ? "loss" : "info"}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <EquityCurveFan result={result.result} />
              <RuinGauge probability={result.result.probability_of_ruin} />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <Histogram
                title="Total return distribution"
                subtitle="Synthetic run outcomes vs real result"
                values={result.result.synthetic.total_return_distribution}
                realValue={result.result.real.total_return}
                formatTick={(v) => `${(v * 100).toFixed(0)}%`}
                color="#4C9EFF"
              />
              <Histogram
                title="Max drawdown distribution"
                subtitle="Fraction of capital lost at the worst point"
                values={result.result.synthetic.max_drawdown_distribution}
                realValue={result.result.real.max_drawdown}
                formatTick={(v) => `${(v * 100).toFixed(0)}%`}
                color="#FF3B5C"
              />
              <Histogram
                title="Sharpe distribution"
                subtitle="Risk-adjusted return, annualized"
                values={result.result.synthetic.sharpe_distribution}
                realValue={result.result.real.sharpe}
                formatTick={(v) => v.toFixed(1)}
                color="#00FF88"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <OverfitGauge percentile={result.result.overfitting_percentile} />
              <ChartCard title="Analyst summary" subtitle="Claude verdict, in one paragraph">
                <p
                  className={`text-sm leading-relaxed ${colorForReturn(result.result.real.total_return)}`}
                >
                  {result.summary}
                </p>
              </ChartCard>
            </div>

            <VerdictPlayer verdict={result.verdict} />
          </>
        )}
      </div>
    </main>
  );
}
