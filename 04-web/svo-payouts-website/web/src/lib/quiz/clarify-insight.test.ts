import { describe, expect, it } from "vitest";
import {
  buildClarifyInsightPayload,
  consultantStepsByPrimaryBlocker,
  formatClarifyTelegramSummaryPlain,
} from "@/lib/quiz/clarify-insight";
import type { QuizAnswers } from "@/types/quiz";

function baseNew(): QuizAnswers {
  return {
    clarifyStage1: "collecting_docs",
    clarifyDeathCert: "yes",
    clarifyMilitaryNotice: "yes",
    clarifyKinshipDocs: "complete",
    clarifyCopiesStatus: "ready",
    clarifyFilingStatus: "not_yet",
    clarifyGoalPrimary: "filing_order",
    clarifyGoalSecondary: "next_steps",
  };
}

describe("buildClarifyInsightPayload", () => {
  it("строит payload для нового квиза без официальной подачи", () => {
    const p = buildClarifyInsightPayload(baseNew());
    expect(p).not.toBeNull();
    expect(p!.stage_score).toBeGreaterThan(0);
    expect(p!.filing_route).toContain("не подавали");
    expect(p!.telegram_summary_plain).toContain("Новая заявка из квиза");
    expect(p!.telegram_summary_plain).toContain("Что сделать консультанту:");
    expect(p!.consultant_step_1).toBeTruthy();
    expect(consultantStepsByPrimaryBlocker[p!.primary_blocker_key].length).toBe(3);
  });

  it("ветка после подачи: refusal → response_after_filing", () => {
    const p = buildClarifyInsightPayload({
      ...baseNew(),
      clarifyFilingStatus: "full_waiting",
      clarifyWhereSubmitted: "military_unit",
      clarifyPostFilingFeedback: "refusal",
    });
    expect(p?.primary_blocker_key).toBe("response_after_filing");
    expect(p?.current_case_state).toContain("отказ");
  });

  it("несколько маршрутов + фокус на порядке → multiple_routes_confusion", () => {
    const p = buildClarifyInsightPayload({
      ...baseNew(),
      clarifyFilingStatus: "full_waiting",
      clarifyWhereSubmitted: "several",
      clarifyPostFilingFeedback: "just_waiting",
      clarifyGoalPrimary: "filing_order",
      clarifyGoalSecondary: "next_steps",
    });
    expect(p?.current_case_state).toContain("несколько мест");
  });

  it("legacy-ответы: had_feedback маппится в инсайт", () => {
    const p = buildClarifyInsightPayload({
      clarifyDeathCert: "yes",
      clarifyMilitaryNotice: "yes",
      clarifyKinshipDocs: "complete",
      clarifyCopiesStatus: "ready",
      clarifyFilingStatus: "had_feedback",
      clarifyWhereSubmitted: "sfr_mfc",
      clarifyConsequenceFocus: "after_authority_response",
    });
    expect(p).not.toBeNull();
    expect(p!.raw_answers.clarifyPostFilingFeedback).toBe("response_unclear");
  });
});

describe("formatClarifyTelegramSummaryPlain", () => {
  it("вторичная строка опускается, если пустая", () => {
    const text = formatClarifyTelegramSummaryPlain({
      stage_label: "Тест",
      stage_score: 50,
      journey_phase: "До подачи",
      lead_temperature: "Тёплый лид",
      death_certificate_status: "есть",
      military_notice_status: "есть",
      kinship_docs_status: "собраны",
      submission_pack_status: "готов",
      filing_status: "Официально не подавали",
      filing_route: "не подавали",
      current_case_state: "Тест состояния",
      primary_blocker: "Стопор",
      secondary_blocker_line: "",
      user_focus: "Фокус",
      consultant_summary: "Кратко.",
      consultant_step_1: "Шаг 1",
      consultant_step_2: "Шаг 2",
      consultant_step_3: "Шаг 3",
    });
    expect(text).not.toMatch(/\n\n\n/);
    expect(text).toContain("— Стопор");
  });
});
