import type { ClarifyFilingStatus, FlowMode, QuizAnswers, QuizStepId } from "@/types/quiz";

const FRESH_PAY_STEPS: QuizStepId[] = [
  "service_status",
  "applicant_role",
  "recipients_count",
  "children_count",
  "death_basis",
  "ambiguity_flag",
  "region",
  "calc_mode",
];

/** Официальная подача уже была (для условных шагов 6–7 цепочки). */
export function clarifyHasOfficialFiling(
  status: ClarifyFilingStatus | undefined,
): boolean {
  if (status == null) return false;
  return status !== "not_yet";
}

export function getClarifyVisibleSteps(answers: QuizAnswers): QuizStepId[] {
  const steps: QuizStepId[] = [
    "clarify_stage_1",
    "clarify_doc_1",
    "clarify_doc_2",
    "clarify_doc_3",
    "clarify_doc_4",
    "clarify_doc_5",
  ];
  if (clarifyHasOfficialFiling(answers.clarifyFilingStatus)) {
    steps.push("clarify_doc_6", "clarify_feedback_1");
  }
  steps.push("clarify_goal_1", "clarify_goal_2");
  return steps;
}

/** Порядок шагов для выбранного режима и ответов. */
export function getVisibleSteps(flowMode: FlowMode, answers: QuizAnswers): QuizStepId[] {
  if (flowMode === "clarify") {
    return getClarifyVisibleSteps(answers);
  }
  return [...FRESH_PAY_STEPS];
}

export function isFreshPayStep(id: QuizStepId): boolean {
  return FRESH_PAY_STEPS.includes(id);
}

export function isClarifyStep(id: QuizStepId): boolean {
  return (
    id === "clarify_stage_1" ||
    id === "clarify_doc_1" ||
    id === "clarify_doc_2" ||
    id === "clarify_doc_3" ||
    id === "clarify_doc_4" ||
    id === "clarify_doc_5" ||
    id === "clarify_doc_6" ||
    id === "clarify_feedback_1" ||
    id === "clarify_goal_1" ||
    id === "clarify_goal_2"
  );
}

export function clampStepIndex(index: number, stepsLength: number): number {
  if (stepsLength <= 0) return 0;
  return Math.max(0, Math.min(index, stepsLength - 1));
}
