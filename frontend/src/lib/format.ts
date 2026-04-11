/**
 * Formatting helpers for numeric display.
 * Keep these tiny — they are pure functions and easy to test in isolation.
 */

export function formatPercent(value: number, digits = 1): string {
  if (!Number.isFinite(value)) {
    return "—";
  }
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatSignedPercent(value: number, digits = 1): string {
  if (!Number.isFinite(value)) {
    return "—";
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(digits)}%`;
}

export function formatNumber(value: number, digits = 2): string {
  if (!Number.isFinite(value)) {
    return "—";
  }
  return value.toFixed(digits);
}

export function formatPercentile(value: number): string {
  if (!Number.isFinite(value)) {
    return "—";
  }
  return `${value.toFixed(1)}°`;
}

export function colorForReturn(value: number): string {
  if (!Number.isFinite(value) || value === 0) {
    return "text-muted";
  }
  return value > 0 ? "text-profit" : "text-loss";
}

export function colorForOverfit(percentile: number): string {
  if (!Number.isFinite(percentile)) {
    return "text-muted";
  }
  if (percentile >= 90) {
    return "text-loss";
  }
  if (percentile >= 70) {
    return "text-info";
  }
  return "text-profit";
}

export function overfitLabel(percentile: number): string {
  if (!Number.isFinite(percentile)) {
    return "Unknown";
  }
  if (percentile >= 90) {
    return "Likely overfit";
  }
  if (percentile >= 70) {
    return "Possibly overfit";
  }
  if (percentile >= 40) {
    return "Robust";
  }
  return "Under-performing";
}
