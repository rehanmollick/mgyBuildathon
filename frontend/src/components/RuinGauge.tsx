import { formatPercent } from "@/lib/format";

import { ChartCard } from "./ChartCard";

export interface RuinGaugeProps {
  readonly probability: number;
}

function colorFor(p: number): string {
  if (p >= 0.25) return "text-loss";
  if (p >= 0.1) return "text-info";
  return "text-profit";
}

function labelFor(p: number): string {
  if (p >= 0.25) return "Dangerous";
  if (p >= 0.1) return "Elevated";
  return "Contained";
}

export function RuinGauge({ probability }: RuinGaugeProps): JSX.Element {
  return (
    <ChartCard
      title="Probability of ruin"
      subtitle="Fraction of synthetic runs that lost more than 50%"
    >
      <div className="flex h-full flex-col items-center justify-center">
        <div className={`text-5xl font-bold ${colorFor(probability)}`}>
          {formatPercent(probability)}
        </div>
        <div className={`mt-2 text-xs font-semibold uppercase tracking-wider ${colorFor(probability)}`}>
          {labelFor(probability)}
        </div>
      </div>
    </ChartCard>
  );
}
