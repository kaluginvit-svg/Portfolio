import { clarifyHasOfficialFiling } from "@/lib/quiz/steps";
import type { QuizAnswers } from "@/types/quiz";

/** Новый квиз «Прояснение ситуации» (10 шагов с ветвлением). */
export function isNewClarifyQuizComplete(answers: QuizAnswers): boolean {
  const filed = clarifyHasOfficialFiling(answers.clarifyFilingStatus);
  return (
    answers.clarifyStage1 != null &&
    answers.clarifyDeathCert != null &&
    answers.clarifyMilitaryNotice != null &&
    answers.clarifyKinshipDocs != null &&
    answers.clarifyCopiesStatus != null &&
    answers.clarifyFilingStatus != null &&
    (!filed ||
      (answers.clarifyWhereSubmitted != null &&
        answers.clarifyWhereSubmitted !== "not_yet" &&
        answers.clarifyPostFilingFeedback != null)) &&
    answers.clarifyGoalPrimary != null &&
    answers.clarifyGoalSecondary != null
  );
}

/** Старые клиенты: 7 шагов до clarify_doc_7. */
export function isLegacyClarifyQuizComplete(answers: QuizAnswers): boolean {
  return (
    answers.clarifyDeathCert != null &&
    answers.clarifyMilitaryNotice != null &&
    answers.clarifyKinshipDocs != null &&
    answers.clarifyCopiesStatus != null &&
    answers.clarifyFilingStatus != null &&
    answers.clarifyWhereSubmitted != null &&
    answers.clarifyConsequenceFocus != null
  );
}

export function isClarifyQuizComplete(answers: QuizAnswers): boolean {
  return isNewClarifyQuizComplete(answers) || isLegacyClarifyQuizComplete(answers);
}
