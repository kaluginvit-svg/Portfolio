import type { QuizAnswers } from "@/types/quiz";

/**
 * Ответы опроса «прояснить ситуацию», которые переносим в полный расчёт,
 * чтобы не терять оценку ожидания и контекст лида после «Перейти к расчёту».
 */
export function preserveClarifyAnswersForFreshFlow(
  answers: QuizAnswers,
): QuizAnswers {
  const next: QuizAnswers = {};
  if (answers.clarifyStage1 != null) {
    next.clarifyStage1 = answers.clarifyStage1;
  }
  if (answers.clarifyDeathCert != null) {
    next.clarifyDeathCert = answers.clarifyDeathCert;
  }
  if (answers.clarifyMilitaryNotice != null) {
    next.clarifyMilitaryNotice = answers.clarifyMilitaryNotice;
  }
  if (answers.clarifyKinshipDocs != null) {
    next.clarifyKinshipDocs = answers.clarifyKinshipDocs;
  }
  if (answers.clarifyCopiesStatus != null) {
    next.clarifyCopiesStatus = answers.clarifyCopiesStatus;
  }
  if (answers.clarifyFilingStatus != null) {
    next.clarifyFilingStatus = answers.clarifyFilingStatus;
  }
  if (answers.clarifyWhereSubmitted != null) {
    next.clarifyWhereSubmitted = answers.clarifyWhereSubmitted;
  }
  if (answers.clarifyConsequenceFocus != null) {
    next.clarifyConsequenceFocus = answers.clarifyConsequenceFocus;
  }
  if (answers.clarifyPostFilingFeedback != null) {
    next.clarifyPostFilingFeedback = answers.clarifyPostFilingFeedback;
  }
  if (answers.clarifyGoalPrimary != null) {
    next.clarifyGoalPrimary = answers.clarifyGoalPrimary;
  }
  if (answers.clarifyGoalSecondary != null) {
    next.clarifyGoalSecondary = answers.clarifyGoalSecondary;
  }
  if (typeof answers.stuckMonthsWaiting === "number") {
    next.stuckMonthsWaiting = answers.stuckMonthsWaiting;
  }
  return next;
}
