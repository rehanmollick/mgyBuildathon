"use client";

import { Fragment, useState } from "react";

import {
  colorForOverfit,
  colorForReturn,
  formatPercentile,
  formatSignedPercent,
} from "@/lib/format";
import type { VariantResult } from "@/lib/types";

export interface LeaderboardTableProps {
  readonly baseline: VariantResult;
  readonly variants: readonly VariantResult[];
}

export function LeaderboardTable({ baseline, variants }: LeaderboardTableProps): JSX.Element {
  const rows: readonly VariantResult[] = [baseline, ...variants];
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div className="overflow-hidden rounded-lg border border-bg-border bg-bg-card">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-bg-border text-left text-xs uppercase tracking-wider text-muted">
            <th className="px-4 py-3 font-medium">Rank</th>
            <th className="px-4 py-3 font-medium">Variant</th>
            <th className="px-4 py-3 text-right font-medium">Real return</th>
            <th className="px-4 py-3 text-right font-medium">Max drawdown</th>
            <th className="px-4 py-3 text-right font-medium">Sharpe</th>
            <th className="px-4 py-3 text-right font-medium">Overfit</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => {
            const isBaseline = row === baseline;
            const isExpanded = expanded === idx;
            return (
              <Fragment key={`row-${idx}`}>
                <tr
                  className={`cursor-pointer border-b border-bg-border transition-colors hover:bg-bg-hover ${
                    isBaseline ? "bg-bg-hover/30" : ""
                  }`}
                  onClick={() => setExpanded(isExpanded ? null : idx)}
                >
                  <td className="px-4 py-3 font-mono text-xs text-muted">
                    {isBaseline ? "base" : `#${row.rank}`}
                  </td>
                  <td className="px-4 py-3 text-white">
                    {row.description}
                    {isBaseline && (
                      <span className="ml-2 rounded bg-info/20 px-2 py-0.5 text-xs font-medium text-info">
                        baseline
                      </span>
                    )}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-mono ${colorForReturn(
                      row.result.real.total_return,
                    )}`}
                  >
                    {formatSignedPercent(row.result.real.total_return)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-loss">
                    {formatSignedPercent(row.result.real.max_drawdown)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-white">
                    {row.result.real.sharpe.toFixed(2)}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-mono font-semibold ${colorForOverfit(
                      row.overfitting_percentile,
                    )}`}
                  >
                    {formatPercentile(row.overfitting_percentile)}
                  </td>
                </tr>
                {isExpanded && (
                  <tr className="border-b border-bg-border bg-bg">
                    <td colSpan={6} className="px-4 py-4">
                      <pre className="scrollbar-thin overflow-x-auto rounded-md border border-bg-border bg-bg-card p-3 font-mono text-xs text-white">
                        <code>{row.code}</code>
                      </pre>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
