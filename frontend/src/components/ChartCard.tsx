import type { ReactNode } from "react";

export interface ChartCardProps {
  readonly title: string;
  readonly subtitle?: string;
  readonly className?: string;
  readonly children: ReactNode;
}

export function ChartCard({ title, subtitle, className, children }: ChartCardProps): JSX.Element {
  return (
    <section
      className={`animate-fade-in flex flex-col rounded-lg border border-bg-border bg-bg-card p-5 ${className ?? ""}`}
    >
      <header className="mb-3">
        <h3 className="text-sm font-semibold text-white">{title}</h3>
        {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
      </header>
      <div className="flex-1">{children}</div>
    </section>
  );
}
