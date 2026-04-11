"use client";

import { useState } from "react";

export interface StrategyInputProps {
  readonly onSubmit: (description: string) => void;
  readonly disabled: boolean;
  readonly buttonLabel?: string;
  readonly placeholder?: string;
}

const PRESETS: ReadonlyArray<{ label: string; description: string }> = [
  {
    label: "MA crossover",
    description:
      "Buy when the 50-day moving average crosses above the 200-day moving average. Sell on the cross below.",
  },
  {
    label: "RSI mean reversion",
    description: "Buy when RSI drops below 30. Sell when RSI crosses above 70.",
  },
  {
    label: "Bollinger Band touch",
    description:
      "Buy when the closing price touches the lower Bollinger Band (20, 2). Sell when it touches the upper band.",
  },
  {
    label: "MACD momentum",
    description:
      "Buy when MACD crosses above the signal line. Sell when MACD crosses below the signal line.",
  },
  {
    label: "Buy and hold",
    description: "Buy on the first day and never sell. Baseline benchmark strategy.",
  },
  {
    label: "3-day reversal",
    description:
      "Buy after three consecutive red candles. Sell after two consecutive green candles.",
  },
  {
    label: "Breakout",
    description:
      "Buy when the closing price exceeds the 20-day high. Sell when it drops below the 20-day low.",
  },
  {
    label: "Volume spike",
    description:
      "Buy when volume exceeds 2x its 20-day average with a green candle. Sell five bars later.",
  },
];

export function StrategyInput({
  onSubmit,
  disabled,
  buttonLabel = "Forge",
  placeholder = "Describe your trading strategy in plain English...",
}: StrategyInputProps): JSX.Element {
  const [value, setValue] = useState<string>("");
  const isValid = value.trim().length >= 10;

  const handleSubmit = (): void => {
    if (isValid && !disabled) {
      onSubmit(value.trim());
    }
  };

  const handlePreset = (preset: string): void => {
    setValue(preset);
  };

  return (
    <div className="animate-fade-in rounded-lg border border-bg-border bg-bg-card p-6">
      <label htmlFor="strategy-description" className="mb-2 block text-sm font-medium text-muted">
        Strategy description
      </label>
      <textarea
        id="strategy-description"
        className="h-28 w-full resize-none rounded-md border border-bg-border bg-bg px-4 py-3 text-sm text-white outline-none transition-colors placeholder:text-muted focus:border-profit"
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
      />
      <div className="mt-4 flex items-center justify-between gap-4">
        <select
          className="rounded-md border border-bg-border bg-bg px-3 py-2 text-sm text-muted focus:border-profit focus:text-white"
          onChange={(e) => {
            if (e.target.value) handlePreset(e.target.value);
          }}
          value=""
          disabled={disabled}
          aria-label="Preset strategies"
        >
          <option value="">Choose a preset…</option>
          {PRESETS.map((preset) => (
            <option key={preset.label} value={preset.description}>
              {preset.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="rounded-md bg-profit px-6 py-2 text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          onClick={handleSubmit}
          disabled={!isValid || disabled}
        >
          {disabled ? "Running…" : buttonLabel}
        </button>
      </div>
    </div>
  );
}
