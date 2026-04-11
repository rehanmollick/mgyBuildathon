"use client";

import { useState } from "react";

import { LeaderboardTable } from "@/components/LeaderboardTable";
import { ProgressSteps, type Step } from "@/components/ProgressSteps";
import { StrategyInput } from "@/components/StrategyInput";
import { TabNav } from "@/components/TabNav";
import { VerdictPlayer } from "@/components/VerdictPlayer";
import { evolve } from "@/lib/api";
import type { EvolveResult } from "@/lib/types";

const STEP_SEQUENCE: readonly Step[] = ["parse", "imagine", "test", "analyze"];

export default function EvolvePage(): JSX.Element {
  const [result, setResult] = useState<EvolveResult | null>(null);
  const [step, setStep] = useState<Step | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState<boolean>(false);

  const handleSubmit = async (description: string): Promise<void> => {
    setError(null);
    setResult(null);
    setRunning(true);
    const animate = async (): Promise<void> => {
      for (const s of STEP_SEQUENCE) {
        setStep(s);
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
    };
    try {
      const [evolved] = await Promise.all([evolve({ description }), animate()]);
      setResult(evolved);
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
          <h1 className="text-2xl font-bold text-white">Evolve a strategy</h1>
          <p className="text-sm text-muted">
            Start from one strategy. We generate ten variants, test each against the same synthetic
            markets, and rank them by robustness instead of raw return.
          </p>
        </header>

        <StrategyInput
          onSubmit={handleSubmit}
          disabled={running}
          buttonLabel="Evolve"
          placeholder="Describe the seed strategy to mutate..."
        />

        {(step !== null || result !== null) && (
          <div className="flex items-center justify-between">
            <ProgressSteps current={step} />
            {error && <span className="text-xs text-loss">{error}</span>}
          </div>
        )}

        {result && (
          <>
            <LeaderboardTable baseline={result.baseline} variants={result.variants} />
            <VerdictPlayer verdict={result.verdict} />
          </>
        )}
      </div>
    </main>
  );
}
