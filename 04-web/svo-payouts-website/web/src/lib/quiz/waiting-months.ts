import type { QuizAnswers } from "@/types/quiz";

/** Оценка месяцев ожидания для блока «цена ожидания» (legacy + clarify). */
export function getEstimatedWaitingMonths(answers: QuizAnswers): number | null {
  const stuck = answers.stuckMonthsWaiting;
  if (typeof stuck === "number" && stuck > 0 && Number.isFinite(stuck)) {
    return stuck;
  }
  switch (answers.waiting) {
    case "lt1m":
      return 1;
    case "1to3m":
      return 2;
    case "3to6m":
      return 4;
    case "gt6m":
      return 6;
    default:
      break;
  }
  switch (answers.clarifyFilingStatus) {
    case "partial":
      return 2;
    case "full_waiting":
    case "had_feedback":
    case "unclear_submission":
      return 4;
    default:
      return null;
  }
}
