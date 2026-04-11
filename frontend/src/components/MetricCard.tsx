export interface MetricCardProps {
  readonly label: string;
  readonly value: string;
  readonly tone?: "profit" | "loss" | "info" | "muted";
}

const TONE: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  profit: "text-profit",
  loss: "text-loss",
  info: "text-info",
  muted: "text-white",
};

export function MetricCard({ label, value, tone = "muted" }: MetricCardProps): JSX.Element {
  return (
    <div className="animate-fade-in rounded-lg border border-bg-border bg-bg-card p-4">
      <div className="text-xs font-medium uppercase tracking-wider text-muted">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${TONE[tone]}`}>{value}</div>
    </div>
  );
}
