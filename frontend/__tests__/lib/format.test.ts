import { describe, expect, it } from "vitest";

import {
  colorForOverfit,
  colorForReturn,
  formatNumber,
  formatPercent,
  formatPercentile,
  formatSignedPercent,
  overfitLabel,
} from "@/lib/format";

describe("formatPercent", () => {
  it("formats positive values", () => {
    expect(formatPercent(0.1234)).toBe("12.3%");
  });
  it("formats negative values", () => {
    expect(formatPercent(-0.05)).toBe("-5.0%");
  });
  it("handles NaN", () => {
    expect(formatPercent(Number.NaN)).toBe("—");
  });
  it("handles Infinity", () => {
    expect(formatPercent(Number.POSITIVE_INFINITY)).toBe("—");
  });
});

describe("formatSignedPercent", () => {
  it("adds a + sign for positive values", () => {
    expect(formatSignedPercent(0.1)).toBe("+10.0%");
  });
  it("keeps the - sign for negative values", () => {
    expect(formatSignedPercent(-0.1)).toBe("-10.0%");
  });
  it("does not sign zero", () => {
    expect(formatSignedPercent(0)).toBe("0.0%");
  });
});

describe("formatNumber", () => {
  it("rounds to two decimals by default", () => {
    expect(formatNumber(1.23456)).toBe("1.23");
  });
  it("respects custom digit count", () => {
    expect(formatNumber(1.23456, 4)).toBe("1.2346");
  });
  it("handles NaN", () => {
    expect(formatNumber(Number.NaN)).toBe("—");
  });
});

describe("formatPercentile", () => {
  it("appends a degree sign", () => {
    expect(formatPercentile(78.4)).toBe("78.4°");
  });
  it("handles NaN", () => {
    expect(formatPercentile(Number.NaN)).toBe("—");
  });
});

describe("colorForReturn", () => {
  it("returns profit color for positives", () => {
    expect(colorForReturn(0.05)).toBe("text-profit");
  });
  it("returns loss color for negatives", () => {
    expect(colorForReturn(-0.01)).toBe("text-loss");
  });
  it("returns muted for zero and non-finite", () => {
    expect(colorForReturn(0)).toBe("text-muted");
    expect(colorForReturn(Number.NaN)).toBe("text-muted");
  });
});

describe("colorForOverfit", () => {
  it("maps >=90 to loss", () => {
    expect(colorForOverfit(95)).toBe("text-loss");
  });
  it("maps 70-89 to info", () => {
    expect(colorForOverfit(75)).toBe("text-info");
  });
  it("maps <70 to profit", () => {
    expect(colorForOverfit(55)).toBe("text-profit");
  });
});

describe("overfitLabel", () => {
  it("labels extreme tails as likely overfit", () => {
    expect(overfitLabel(95)).toBe("Likely overfit");
  });
  it("labels high but not extreme tails", () => {
    expect(overfitLabel(80)).toBe("Possibly overfit");
  });
  it("labels the healthy middle as robust", () => {
    expect(overfitLabel(50)).toBe("Robust");
  });
  it("labels the lower tail as under-performing", () => {
    expect(overfitLabel(10)).toBe("Under-performing");
  });
});
