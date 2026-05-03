import { describe, expect, it } from "vitest";
import { validateQuizStep } from "@/lib/quiz/validate-quiz-step";
import type { QuizAnswers, QuizStepId } from "@/types/quiz";

describe("validateQuizStep (fresh pay)", () => {
  it("service_status", () => {
    expect(validateQuizStep("service_status", {})).not.toBeNull();
    expect(validateQuizStep("service_status", { serviceStatus: "volunteer" })).toBeNull();
  });

  it("applicant_role", () => {
    expect(validateQuizStep("applicant_role", {})).not.toBeNull();
    expect(
      validateQuizStep("applicant_role", { freshApplicantRole: "parent" }),
    ).toBeNull();
  });

  it("recipients_count + children_count", () => {
    expect(validateQuizStep("recipients_count", {})).not.toBeNull();
    expect(
      validateQuizStep("recipients_count", { freshRecipientsCount: "2" }),
    ).toBeNull();
    expect(validateQuizStep("children_count", {})).not.toBeNull();
    expect(validateQuizStep("children_count", { freshChildrenCount: "0" })).toBeNull();
  });

  it("death_basis + ambiguity_flag + calc_mode", () => {
    expect(validateQuizStep("death_basis", {})).not.toBeNull();
    expect(validateQuizStep("death_basis", { deathBasis: "duty" })).toBeNull();
    expect(validateQuizStep("ambiguity_flag", {})).not.toBeNull();
    expect(validateQuizStep("ambiguity_flag", { ambiguityFlag: "no" })).toBeNull();
    expect(validateQuizStep("calc_mode", {})).not.toBeNull();
    expect(validateQuizStep("calc_mode", { calcMode: "federal_only" })).toBeNull();
  });

  it("region: длина >= 2", () => {
    expect(validateQuizStep("region", { region: "x" })).not.toBeNull();
    expect(validateQuizStep("region", { region: "Москва" })).toBeNull();
  });

  it("clarify: обязательные поля по шагам", () => {
    const ids: QuizStepId[] = [
      "clarify_stage_1",
      "clarify_doc_1",
      "clarify_doc_2",
      "clarify_doc_3",
      "clarify_doc_4",
      "clarify_doc_5",
      "clarify_goal_1",
      "clarify_goal_2",
    ];
    for (const id of ids) {
      expect(validateQuizStep(id, {}), id).not.toBeNull();
    }
  });

  it("clarify: полный снимок без подачи — ок на каждом видимом шаге", () => {
    const a: QuizAnswers = {
      clarifyStage1: "start",
      clarifyDeathCert: "yes",
      clarifyMilitaryNotice: "yes",
      clarifyKinshipDocs: "complete",
      clarifyCopiesStatus: "ready",
      clarifyFilingStatus: "not_yet",
      clarifyGoalPrimary: "no_start",
      clarifyGoalSecondary: "next_steps",
    };
    expect(validateQuizStep("clarify_stage_1", a)).toBeNull();
    expect(validateQuizStep("clarify_doc_5", a)).toBeNull();
    expect(validateQuizStep("clarify_goal_2", a)).toBeNull();
  });

  it("clarify_doc_6 и clarify_feedback_1 только при подаче", () => {
    const a: QuizAnswers = {
      clarifyStage1: "already_filed",
      clarifyDeathCert: "yes",
      clarifyMilitaryNotice: "yes",
      clarifyKinshipDocs: "complete",
      clarifyCopiesStatus: "ready",
      clarifyFilingStatus: "not_yet",
      clarifyGoalPrimary: "after_filing",
      clarifyGoalSecondary: "find_blocker",
    };
    expect(validateQuizStep("clarify_doc_6", a)).toBeNull();
    expect(validateQuizStep("clarify_feedback_1", a)).toBeNull();
  });

  it("clarify_doc_6: not_yet как маршрут — ошибка", () => {
    const a: QuizAnswers = {
      clarifyFilingStatus: "partial",
      clarifyWhereSubmitted: "not_yet",
    };
    expect(validateQuizStep("clarify_doc_6", a)).not.toBeNull();
  });
});
