import { describe, expect, it } from "vitest";
import { getEstimatedWaitingMonths } from "@/lib/quiz/waiting-months";
import { preserveClarifyAnswersForFreshFlow } from "@/lib/quiz/preserve-clarify-for-fresh";
import type { QuizAnswers } from "@/types/quiz";

describe("preserveClarifyAnswersForFreshFlow", () => {
  it("переносит только clarify и stuckMonthsWaiting, сбрасывает остальное", () => {
    const before: QuizAnswers = {
      deceasedRole: "mobilized",
      clarifyStage1: "already_filed",
      clarifyFilingStatus: "full_waiting",
      clarifyDeathCert: "yes",
      clarifyPostFilingFeedback: "just_waiting",
      clarifyGoalPrimary: "after_filing",
      clarifyGoalSecondary: "find_blocker",
      clarifyConsequenceFocus: "timelines_stages",
      stuckMonthsWaiting: 6,
      region: "Старый регион",
    };
    const kept = preserveClarifyAnswersForFreshFlow(before);
    expect(kept).toEqual({
      clarifyStage1: "already_filed",
      clarifyDeathCert: "yes",
      clarifyFilingStatus: "full_waiting",
      clarifyPostFilingFeedback: "just_waiting",
      clarifyGoalPrimary: "after_filing",
      clarifyGoalSecondary: "find_blocker",
      clarifyConsequenceFocus: "timelines_stages",
      stuckMonthsWaiting: 6,
    });
    expect(kept.deceasedRole).toBeUndefined();
    expect(kept.region).toBeUndefined();
  });

  it("после переноса getEstimatedWaitingMonths всё ещё видит clarify", () => {
    const kept = preserveClarifyAnswersForFreshFlow({
      clarifyFilingStatus: "partial",
    });
    const merged: QuizAnswers = {
      ...kept,
      deceasedRole: "contract",
      relation: "spouse",
      recipients: "only_me",
      documents: ["death_cert"],
      region: "Москва",
    };
    expect(getEstimatedWaitingMonths(merged)).toBe(2);
  });
});
