import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProgressSteps } from "@/components/ProgressSteps";

describe("ProgressSteps", () => {
  it("renders all four step labels", () => {
    render(<ProgressSteps current={null} />);
    expect(screen.getByText("Parse")).toBeInTheDocument();
    expect(screen.getByText("Imagine")).toBeInTheDocument();
    expect(screen.getByText("Test")).toBeInTheDocument();
    expect(screen.getByText("Analyze")).toBeInTheDocument();
  });

  it("marks the current step with aria-current", () => {
    render(<ProgressSteps current="imagine" />);
    const current = screen.getByText("2");
    expect(current).toHaveAttribute("aria-current", "step");
  });

  it("renders a check mark for completed steps", () => {
    render(<ProgressSteps current="test" />);
    const checks = screen.getAllByText("✓");
    expect(checks.length).toBeGreaterThanOrEqual(2);
  });

  it('marks every step complete when current is "done"', () => {
    render(<ProgressSteps current="done" />);
    const checks = screen.getAllByText("✓");
    expect(checks.length).toBe(4);
  });
});
