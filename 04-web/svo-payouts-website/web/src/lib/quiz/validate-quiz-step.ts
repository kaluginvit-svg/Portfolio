import { quizFlowCopy } from "@/data/texts/quiz-copy";
import { clarifyHasOfficialFiling } from "@/lib/quiz/steps";
import type { QuizAnswers, QuizStepId } from "@/types/quiz";

/** Проверка шага по переданному снимку ответов (для мгновенного перехода в clarify). */
export function validateQuizStep(id: QuizStepId | undefined, a: QuizAnswers): string | null {
  if (!id) return null;
  switch (id) {
    case "clarify_stage_1":
      return a.clarifyStage1 ? null : quizFlowCopy.validation.pickOne;
    case "clarify_doc_1":
      return a.clarifyDeathCert ? null : quizFlowCopy.validation.pickOne;
    case "clarify_doc_2":
      return a.clarifyMilitaryNotice ? null : quizFlowCopy.validation.pickOne;
    case "clarify_doc_3":
      return a.clarifyKinshipDocs ? null : quizFlowCopy.validation.pickOne;
    case "clarify_doc_4":
      return a.clarifyCopiesStatus ? null : quizFlowCopy.validation.pickOne;
    case "clarify_doc_5":
      return a.clarifyFilingStatus ? null : quizFlowCopy.validation.pickOne;
    case "clarify_doc_6":
      if (!clarifyHasOfficialFiling(a.clarifyFilingStatus)) return null;
      return a.clarifyWhereSubmitted &&
        a.clarifyWhereSubmitted !== "not_yet"
        ? null
        : quizFlowCopy.validation.pickOne;
    case "clarify_feedback_1":
      if (!clarifyHasOfficialFiling(a.clarifyFilingStatus)) return null;
      return a.clarifyPostFilingFeedback ? null : quizFlowCopy.validation.pickOne;
    case "clarify_goal_1":
      return a.clarifyGoalPrimary ? null : quizFlowCopy.validation.pickOne;
    case "clarify_goal_2":
      return a.clarifyGoalSecondary ? null : quizFlowCopy.validation.pickOne;
    case "service_status":
      return a.serviceStatus ? null : quizFlowCopy.validation.pickOne;
    case "applicant_role":
      return a.freshApplicantRole ? null : quizFlowCopy.validation.pickOne;
    case "recipients_count":
      return a.freshRecipientsCount ? null : quizFlowCopy.validation.pickOne;
    case "children_count":
      return a.freshChildrenCount != null ? null : quizFlowCopy.validation.pickOne;
    case "death_basis":
      return a.deathBasis ? null : quizFlowCopy.validation.pickOne;
    case "ambiguity_flag":
      return a.ambiguityFlag ? null : quizFlowCopy.validation.pickOne;
    case "calc_mode":
      return a.calcMode ? null : quizFlowCopy.validation.pickOne;
    case "region": {
      const r = (a.region ?? "").trim();
      if (r.length < 2) return quizFlowCopy.validation.regionShort;
      return null;
    }
    default:
      return null;
  }
}
