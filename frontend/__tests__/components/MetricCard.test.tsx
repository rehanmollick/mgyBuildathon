import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MetricCard } from "@/components/MetricCard";

describe("MetricCard", () => {
  it("renders label and value", () => {
    render(<MetricCard label="Sharpe" value="1.62" />);
    expect(screen.getByText("Sharpe")).toBeInTheDocument();
    expect(screen.getByText("1.62")).toBeInTheDocument();
  });

  it("applies the profit tone class", () => {
    const { container } = render(
      <MetricCard label="Real return" value="+12%" tone="profit" />,
    );
    const valueNode = container.querySelector(".text-profit");
    expect(valueNode).not.toBeNull();
  });

  it("applies the loss tone class", () => {
    const { container } = render(
      <MetricCard label="Drawdown" value="-34%" tone="loss" />,
    );
    const valueNode = container.querySelector(".text-loss");
    expect(valueNode).not.toBeNull();
  });
});
