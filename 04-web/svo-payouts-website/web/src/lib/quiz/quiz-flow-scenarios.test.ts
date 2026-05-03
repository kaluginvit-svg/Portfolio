import { describe, expect, it } from "vitest";
import { getVisibleSteps } from "@/lib/quiz/steps";
import { validateQuizStep } from "@/lib/quiz/validate-quiz-step";
import type { QuizAnswers } from "@/types/quiz";

/**
 * Снимки «полных» ответов: каждый шаг видимой цепочки должен валидироваться без ошибки.
 * Дополняет точечные тесты validate-quiz-step (сквозные сценарии).
 */
describe("quiz flow scenarios (сквозная валидация)", () => {
  it("fresh: полный снимок (стандартная ветка)", () => {
    const a: QuizAnswers = {
      serviceStatus: "contract_mobilized",
      freshApplicantRole: "spouse_registered",
      freshRecipientsCount: "1",
      freshChildrenCount: "0",
      deathBasis: "duty",
      ambiguityFlag: "no",
      region: "Московская область",
      calcMode: "federal_only",
    };
    const steps = getVisibleSteps("fresh", a);
    expect(steps).toHaveLength(8);
    for (const id of steps) {
      expect(validateQuizStep(id, a), `step ${id}`).toBeNull();
    }
  });

  it("fresh: спорная ветка + 5+ получателей + дети", () => {
    const a: QuizAnswers = {
      serviceStatus: "contract_mobilized",
      freshApplicantRole: "cohabitation_no_marriage",
      freshRecipientsCount: "5_plus",
      freshChildrenCount: "3_plus",
      deathBasis: "unknown",
      ambiguityFlag: "yes",
      region: "Санкт-Петербург",
      calcMode: "federal_plus_region",
    };
    const steps = getVisibleSteps("fresh", a);
    expect(steps).toHaveLength(8);
    for (const id of steps) {
      expect(validateQuizStep(id, a), `step ${id}`).toBeNull();
    }
  });

  it("clarify: все поля заполнены (новый квиз, с подачей)", () => {
    const a: QuizAnswers = {
      clarifyStage1: "already_filed",
      clarifyDeathCert: "yes",
      clarifyMilitaryNotice: "requested_waiting",
      clarifyKinshipDocs: "partial",
      clarifyCopiesStatus: "collecting",
      clarifyFilingStatus: "full_waiting",
      clarifyWhereSubmitted: "sfr_mfc",
      clarifyPostFilingFeedback: "just_waiting",
      clarifyGoalPrimary: "missing_docs",
      clarifyGoalSecondary: "check_package",
    };
    const steps = getVisibleSteps("clarify", a);
    expect(steps).toHaveLength(10);
    for (const id of steps) {
      expect(validateQuizStep(id, a), `step ${id}`).toBeNull();
    }
  });
});
