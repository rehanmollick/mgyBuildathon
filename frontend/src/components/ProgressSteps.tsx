"use client";

export type Step = "parse" | "imagine" | "test" | "analyze" | "done";

const STEPS: ReadonlyArray<{ key: Step; label: string }> = [
  { key: "parse", label: "Parse" },
  { key: "imagine", label: "Imagine" },
  { key: "test", label: "Test" },
  { key: "analyze", label: "Analyze" },
];

export interface ProgressStepsProps {
  readonly current: Step | null;
}

function stepIndex(step: Step): number {
  return STEPS.findIndex((s) => s.key === step);
}

export function ProgressSteps({ current }: ProgressStepsProps): JSX.Element {
  const currentIdx = current ? (current === "done" ? STEPS.length : stepIndex(current)) : -1;
  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, i) => {
        const isActive = i === currentIdx;
        const isDone = i < currentIdx;
        return (
          <div key={step.key} className="flex items-center gap-2">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full border text-xs font-semibold transition-colors ${
                isDone
                  ? "border-profit bg-profit text-black"
                  : isActive
                    ? "animate-pulse-profit border-profit text-profit"
                    : "border-bg-border text-muted"
              }`}
              aria-current={isActive ? "step" : undefined}
            >
              {isDone ? "✓" : i + 1}
            </div>
            <span
              className={`text-xs font-medium ${isDone || isActive ? "text-white" : "text-muted"}`}
            >
              {step.label}
            </span>
            {i < STEPS.length - 1 && (
              <div className={`h-px w-6 ${isDone ? "bg-profit" : "bg-bg-border"}`} aria-hidden />
            )}
          </div>
        );
      })}
    </div>
  );
}
