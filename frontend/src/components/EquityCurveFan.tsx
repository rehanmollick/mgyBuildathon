"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { BacktestResult } from "@/lib/types";

import { ChartCard } from "./ChartCard";

export interface EquityCurveFanProps {
  readonly result: BacktestResult;
}

export function EquityCurveFan({ result }: EquityCurveFanProps): JSX.Element {
  const bands = result.synthetic.percentile_bands;
  const real = result.real.equity_curve;
  const n = bands.timestamps.length;

  const data = Array.from({ length: n }, (_, i) => ({
    t: bands.timestamps[i],
    p05: bands.p05[i],
    p50: bands.p50[i],
    p95: bands.p95[i],
    band: (bands.p95[i] ?? 0) - (bands.p05[i] ?? 0),
    real: i < real.length ? real[i] : undefined,
  }));

  return (
    <ChartCard
      title="Equity curve — real vs 200 synthetic markets"
      subtitle="Shaded region is the 5th–95th percentile envelope across synthetic runs."
      className="col-span-2"
    >
      <div className="h-[340px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data}>
            <defs>
              <linearGradient id="bandFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4C9EFF" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#4C9EFF" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#23232e" strokeDasharray="3 3" />
            <XAxis
              dataKey="t"
              tick={{ fill: "#6B6B7B", fontSize: 10 }}
              tickMargin={8}
              minTickGap={40}
            />
            <YAxis
              tick={{ fill: "#6B6B7B", fontSize: 10 }}
              domain={["dataMin - 0.02", "dataMax + 0.02"]}
              tickFormatter={(v: number) => v.toFixed(2)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#12121A",
                border: "1px solid #23232e",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: "#6B6B7B" }}
            />
            <Area
              type="monotone"
              dataKey="p05"
              stroke="transparent"
              fill="transparent"
              stackId="band"
            />
            <Area
              type="monotone"
              dataKey="band"
              stroke="transparent"
              fill="url(#bandFill)"
              stackId="band"
            />
            <Line
              type="monotone"
              dataKey="p50"
              stroke="#4C9EFF"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
              name="Synthetic median"
            />
            <Line
              type="monotone"
              dataKey="real"
              stroke="#00FF88"
              strokeWidth={2.5}
              dot={false}
              name="Real market"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
