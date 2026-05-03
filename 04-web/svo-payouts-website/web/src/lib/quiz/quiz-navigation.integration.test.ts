import { describe, expect, it } from "vitest";
import { preserveClarifyAnswersForFreshFlow } from "@/lib/quiz/preserve-clarify-for-fresh";
import { clampStepIndex, getVisibleSteps } from "@/lib/quiz/steps";
import { validateQuizStep } from "@/lib/quiz/validate-quiz-step";
import type { QuizAnswers } from "@/types/quiz";

describe("quiz navigation (integration)", () => {
  it("fresh: всегда 8 шагов", () => {
    expect(getVisibleSteps("fresh", {}).length).toBe(8);
    expect(getVisibleSteps("fresh", {})[0]).toBe("service_status");
    expect(getVisibleSteps("fresh", {})[7]).toBe("calc_mode");
  });

  it("clarify: базовая цепочка 8 шагов без подачи", () => {
    expect(getVisibleSteps("clarify", {}).length).toBe(8);
  });

  it("clampStepIndex", () => {
    expect(clampStepIndex(5, 3)).toBe(2);
    expect(clampStepIndex(-1, 5)).toBe(0);
    expect(clampStepIndex(0, 0)).toBe(0);
  });

  it("переключение контекста clarify→fresh: сохраняются clarify-поля для следующей цепочки", () => {
    const afterClarify: QuizAnswers = {
      clarifyFilingStatus: "full_waiting",
      clarifyWhereSubmitted: "sfr_mfc",
    };
    const preserved = preserveClarifyAnswersForFreshFlow(afterClarify);
    const merged: QuizAnswers = {
      ...preserved,
      serviceStatus: "contract_mobilized",
      freshApplicantRole: "spouse_registered",
      freshRecipientsCount: "1",
      freshChildrenCount: "0",
      deathBasis: "duty",
      ambiguityFlag: "no",
      calcMode: "federal_only",
      region: "Москва",
    };
    const steps = getVisibleSteps("fresh", merged);
    expect(steps[0]).toBe("service_status");
    expect(validateQuizStep("region", merged)).toBeNull();
  });
});
