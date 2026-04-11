import { colorForOverfit, formatPercentile, overfitLabel } from "@/lib/format";

import { ChartCard } from "./ChartCard";

export interface OverfitGaugeProps {
  readonly percentile: number;
}

export function OverfitGauge({ percentile }: OverfitGaugeProps): JSX.Element {
  const color = colorForOverfit(percentile);
  const label = overfitLabel(percentile);
  const pct = Math.max(0, Math.min(100, percentile));
  return (
    <ChartCard
      title="Overfitting percentile"
      subtitle="Where the real result lands in the synthetic distribution"
    >
      <div className="flex h-full flex-col items-center justify-center">
        <div className={`text-5xl font-bold ${color}`}>{formatPercentile(percentile)}</div>
        <div className={`mt-2 text-xs font-semibold uppercase tracking-wider ${color}`}>
          {label}
        </div>
        <div className="mt-4 h-2 w-full rounded-full bg-bg-border">
          <div
            className={`h-2 rounded-full transition-all ${
              percentile >= 90 ? "bg-loss" : percentile >= 70 ? "bg-info" : "bg-profit"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </ChartCard>
  );
}
