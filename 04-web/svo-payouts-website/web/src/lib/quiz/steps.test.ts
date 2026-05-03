import { describe, expect, it } from "vitest";
import { getVisibleSteps, isClarifyStep, isFreshPayStep, clampStepIndex } from "@/lib/quiz/steps";
import type { QuizAnswers } from "@/types/quiz";

const FRESH_EIGHT: string[] = [
  "service_status",
  "applicant_role",
  "recipients_count",
  "children_count",
  "death_basis",
  "ambiguity_flag",
  "region",
  "calc_mode",
];

describe("getVisibleSteps", () => {
  it("fresh: фиксированные 8 шагов независимо от ответов", () => {
    const a: QuizAnswers = {
      serviceStatus: "contract_mobilized",
      freshApplicantRole: "spouse_registered",
    };
    expect(getVisibleSteps("fresh", a)).toEqual(FRESH_EIGHT);
    expect(getVisibleSteps("fresh", {})).toEqual(FRESH_EIGHT);
  });

  it("clarify: без подачи — 8 шагов", () => {
    expect(getVisibleSteps("clarify", {})).toHaveLength(8);
    expect(getVisibleSteps("clarify", {})[0]).toBe("clarify_stage_1");
    expect(getVisibleSteps("clarify", {})[7]).toBe("clarify_goal_2");
  });

  it("clarify: после подачи добавляет doc_6 и feedback", () => {
    const steps = getVisibleSteps("clarify", { clarifyFilingStatus: "partial" });
    expect(steps).toHaveLength(10);
    expect(steps).toContain("clarify_doc_6");
    expect(steps).toContain("clarify_feedback_1");
  });
});

describe("isClarifyStep / isFreshPayStep", () => {
  it("определяет шаги clarify и fresh", () => {
    expect(isClarifyStep("clarify_doc_1")).toBe(true);
    expect(isClarifyStep("clarify_feedback_1")).toBe(true);
    expect(isClarifyStep("service_status")).toBe(false);
    expect(isFreshPayStep("service_status")).toBe(true);
    expect(isFreshPayStep("calc_mode")).toBe(true);
    expect(isFreshPayStep("clarify_doc_1")).toBe(false);
  });
});

describe("clampStepIndex", () => {
  it("ограничивает индекс", () => {
    expect(clampStepIndex(5, 3)).toBe(2);
    expect(clampStepIndex(-1, 5)).toBe(0);
    expect(clampStepIndex(0, 0)).toBe(0);
  });
});
