import { describe, expect, it } from "vitest";
import {
  isClarifyQuizComplete,
  isLegacyClarifyQuizComplete,
  isNewClarifyQuizComplete,
} from "@/lib/quiz/clarify-complete";
import type { QuizAnswers } from "@/types/quiz";

const newFullNotFiled: QuizAnswers = {
  clarifyStage1: "collecting_docs",
  clarifyDeathCert: "yes",
  clarifyMilitaryNotice: "yes",
  clarifyKinshipDocs: "complete",
  clarifyCopiesStatus: "collecting",
  clarifyFilingStatus: "not_yet",
  clarifyGoalPrimary: "missing_docs",
  clarifyGoalSecondary: "check_package",
};

const newFullFiled: QuizAnswers = {
  ...newFullNotFiled,
  clarifyFilingStatus: "full_waiting",
  clarifyWhereSubmitted: "sfr_mfc",
  clarifyPostFilingFeedback: "just_waiting",
};

const legacyFull: QuizAnswers = {
  clarifyDeathCert: "yes",
  clarifyMilitaryNotice: "yes",
  clarifyKinshipDocs: "complete",
  clarifyCopiesStatus: "ready",
  clarifyFilingStatus: "not_yet",
  clarifyWhereSubmitted: "not_yet",
  clarifyConsequenceFocus: "full_overview",
};

describe("isNewClarifyQuizComplete", () => {
  it("полный путь без подачи — без where и feedback", () => {
    expect(isNewClarifyQuizComplete(newFullNotFiled)).toBe(true);
  });

  it("после подачи требует маршрут и feedback", () => {
    expect(
      isNewClarifyQuizComplete({
        ...newFullFiled,
        clarifyWhereSubmitted: undefined,
      }),
    ).toBe(false);
    expect(isNewClarifyQuizComplete(newFullFiled)).toBe(true);
  });

  it("not_yet на маршруте при подаче не принимается", () => {
    expect(
      isNewClarifyQuizComplete({
        ...newFullFiled,
        clarifyWhereSubmitted: "not_yet",
      }),
    ).toBe(false);
  });
});

describe("isLegacyClarifyQuizComplete", () => {
  it("старый набор полей", () => {
    expect(isLegacyClarifyQuizComplete(legacyFull)).toBe(true);
  });
});

describe("isClarifyQuizComplete", () => {
  it("объединяет новый и legacy", () => {
    expect(isClarifyQuizComplete(newFullNotFiled)).toBe(true);
    expect(isClarifyQuizComplete(legacyFull)).toBe(true);
  });
});
