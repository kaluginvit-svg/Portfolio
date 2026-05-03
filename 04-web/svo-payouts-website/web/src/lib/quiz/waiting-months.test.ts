import { describe, expect, it } from "vitest";
import { getEstimatedWaitingMonths } from "@/lib/quiz/waiting-months";

describe("getEstimatedWaitingMonths", () => {
  it("приоритет stuckMonthsWaiting", () => {
    expect(getEstimatedWaitingMonths({ stuckMonthsWaiting: 6 })).toBe(6);
    expect(getEstimatedWaitingMonths({ stuckMonthsWaiting: 0 })).toBeNull();
  });

  it("legacy waiting", () => {
    expect(getEstimatedWaitingMonths({ waiting: "lt1m" })).toBe(1);
    expect(getEstimatedWaitingMonths({ waiting: "1to3m" })).toBe(2);
    expect(getEstimatedWaitingMonths({ waiting: "3to6m" })).toBe(4);
    expect(getEstimatedWaitingMonths({ waiting: "gt6m" })).toBe(6);
  });

  it("clarify filing", () => {
    expect(getEstimatedWaitingMonths({ clarifyFilingStatus: "partial" })).toBe(2);
    expect(getEstimatedWaitingMonths({ clarifyFilingStatus: "full_waiting" })).toBe(4);
    expect(getEstimatedWaitingMonths({ clarifyFilingStatus: "had_feedback" })).toBe(4);
    expect(getEstimatedWaitingMonths({ clarifyFilingStatus: "unclear_submission" })).toBe(4);
    expect(getEstimatedWaitingMonths({ clarifyFilingStatus: "not_yet" })).toBeNull();
  });
});
