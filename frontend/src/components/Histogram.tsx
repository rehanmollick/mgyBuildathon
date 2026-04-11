"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "./ChartCard";

export interface HistogramProps {
  readonly title: string;
  readonly subtitle?: string;
  readonly values: readonly number[];
  readonly realValue: number;
  readonly formatTick: (value: number) => string;
  readonly bins?: number;
  readonly color?: string;
}

function histogram(values: readonly number[], bins: number): { x: number; count: number }[] {
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return [{ x: min, count: values.length }];
  }
  const step = (max - min) / bins;
  const buckets: { x: number; count: number }[] = Array.from({ length: bins }, (_, i) => ({
    x: min + step * (i + 0.5),
    count: 0,
  }));
  for (const v of values) {
    let idx = Math.floor((v - min) / step);
    if (idx >= bins) idx = bins - 1;
    buckets[idx]!.count += 1;
  }
  return buckets;
}

export function Histogram({
  title,
  subtitle,
  values,
  realValue,
  formatTick,
  bins = 24,
  color = "#4C9EFF",
}: HistogramProps): JSX.Element {
  const data = histogram(values, bins);
  return (
    <ChartCard title={title} subtitle={subtitle}>
      <div className="h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="#23232e" strokeDasharray="3 3" />
            <XAxis
              dataKey="x"
              tick={{ fill: "#6B6B7B", fontSize: 10 }}
              tickFormatter={formatTick}
              minTickGap={20}
            />
            <YAxis tick={{ fill: "#6B6B7B", fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#12121A",
                border: "1px solid #23232e",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelFormatter={(value: number) => formatTick(value)}
            />
            <Bar dataKey="count" fill={color} opacity={0.7} />
            <ReferenceLine
              x={realValue}
              stroke="#00FF88"
              strokeWidth={2}
              label={{ value: "real", position: "top", fill: "#00FF88", fontSize: 10 }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
