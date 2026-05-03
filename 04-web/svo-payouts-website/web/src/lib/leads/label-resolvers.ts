import {
  deceasedOptions,
  documentOptions,
  relationComplexOptions,
  relationOptions,
  statusNowOptions,
  submittedWhereOptions,
} from "@/data/texts/quiz-copy";
import {
  clarifyCopiesOptions,
  clarifyDeathCertOptions,
  clarifyFilingOptions,
  clarifyGoalPrimaryOptions,
  clarifyGoalSecondaryOptions,
  clarifyKinshipOptions,
  clarifyMilitaryNoticeOptions,
  clarifyPostFilingFeedbackOptions,
  clarifyStage1Options,
  clarifyWhereOptions,
  clarifyWhereSubmittedOnlyOptions,
} from "@/data/texts/clarify-quiz-copy";
import {
  ambiguityFlagOptions,
  calcModeOptions,
  deathBasisOptions,
  freshApplicantRoleOptions,
  freshChildrenCountOptions,
  freshRecipientsCountOptions,
  serviceStatusOptions,
} from "@/data/texts/fresh-quiz-copy";
import {
  stuckProblemOptions,
  stuckSubmittedItemOptions,
  stuckSubmittedToOptions,
} from "@/data/texts/stuck-quiz-copy";
import type { QuizAnswers } from "@/types/quiz";

function pickLabel<T extends string>(
  rows: readonly { id: T; label: string }[],
  id: T | undefined,
): string | null {
  if (id === undefined) return null;
  return rows.find((r) => r.id === id)?.label ?? id;
}

export function resolveStatusOfDeceased(answers: QuizAnswers): string | null {
  return pickLabel(deceasedOptions, answers.deceasedRole);
}

export function resolveApplicantRole(answers: QuizAnswers): string | null {
  return pickLabel(relationOptions, answers.relation);
}

export function resolveComplexStatus(answers: QuizAnswers): string | null {
  if (answers.relation !== "complex") return null;
  return pickLabel(relationComplexOptions, answers.relationComplexSub);
}

export function resolveDocumentsOnHand(answers: QuizAnswers): string | null {
  const ids = answers.documents;
  if (!ids?.length) return null;
  const parts = ids.map(
    (id) => documentOptions.find((d) => d.id === id)?.label ?? id,
  );
  return parts.join("; ");
}

/** Краткая сводка нового квиза расчёта выплат (для лида / CRM). */
export function resolveFreshQuizSummary(answers: QuizAnswers): string | null {
  const parts: string[] = [];
  const s0 = pickLabel(serviceStatusOptions, answers.serviceStatus);
  const s1 = pickLabel(freshApplicantRoleOptions, answers.freshApplicantRole);
  const s2 = pickLabel(freshRecipientsCountOptions, answers.freshRecipientsCount);
  const s3 = pickLabel(freshChildrenCountOptions, answers.freshChildrenCount);
  const s4 = pickLabel(deathBasisOptions, answers.deathBasis);
  const s5 = pickLabel(ambiguityFlagOptions, answers.ambiguityFlag);
  const s6 = pickLabel(calcModeOptions, answers.calcMode);
  const reg = answers.region?.trim();
  if (s0) parts.push(`Категория погибшего: ${s0}`);
  if (s1) parts.push(`Заявитель: ${s1}`);
  if (s2) parts.push(`Получатели разовых выплат: ${s2}`);
  if (s3) parts.push(`Дети (ежемесячный блок): ${s3}`);
  if (s4) parts.push(`Основание: ${s4}`);
  if (s5) parts.push(`Спор/неясность: ${s5}`);
  if (reg) parts.push(`Регион: ${reg}`);
  if (s6) parts.push(`Режим расчёта: ${s6}`);
  return parts.length ? parts.join(". ") : null;
}

/** Сводка по блоку «Прояснить ситуацию»: документы, подача, фокус разбора. */
export function resolveClarifyDocumentsSummary(answers: QuizAnswers): string | null {
  const parts: string[] = [];
  const d0 = pickLabel(clarifyStage1Options, answers.clarifyStage1);
  const d1 = pickLabel(clarifyDeathCertOptions, answers.clarifyDeathCert);
  const d2 = pickLabel(clarifyMilitaryNoticeOptions, answers.clarifyMilitaryNotice);
  const d3 = pickLabel(clarifyKinshipOptions, answers.clarifyKinshipDocs);
  const d4 = pickLabel(clarifyCopiesOptions, answers.clarifyCopiesStatus);
  const d5 = pickLabel(clarifyFilingOptions, answers.clarifyFilingStatus);
  const d6 =
    answers.clarifyWhereSubmitted &&
    answers.clarifyWhereSubmitted !== "not_yet"
      ? pickLabel(clarifyWhereSubmittedOnlyOptions, answers.clarifyWhereSubmitted)
      : pickLabel(clarifyWhereOptions, answers.clarifyWhereSubmitted);
  const d8 = pickLabel(clarifyPostFilingFeedbackOptions, answers.clarifyPostFilingFeedback);
  const d9 = pickLabel(clarifyGoalPrimaryOptions, answers.clarifyGoalPrimary);
  const d10 = pickLabel(clarifyGoalSecondaryOptions, answers.clarifyGoalSecondary);
  if (d0) parts.push(`Ситуация: ${d0}`);
  if (d1) parts.push(`Свидетельство о смерти: ${d1}`);
  if (d2) parts.push(`Документ из части: ${d2}`);
  if (d3) parts.push(`Родство: ${d3}`);
  if (d4) parts.push(`Пакет для подачи: ${d4}`);
  if (d5) parts.push(`Официальная подача: ${d5}`);
  if (d6) parts.push(`Куда подавали: ${d6}`);
  if (d8) parts.push(`После подачи: ${d8}`);
  if (d9) parts.push(`Что мешает: ${d9}`);
  if (d10) parts.push(`Что нужнее: ${d10}`);
  return parts.length ? parts.join(". ") : null;
}

/** Устаревший сценарий B. */
export function resolveProblemType(answers: QuizAnswers): string | null {
  return pickLabel(statusNowOptions, answers.statusNow);
}

/** Устаревший сценарий B. */
export function resolveSubmittedTo(answers: QuizAnswers): string | null {
  return pickLabel(submittedWhereOptions, answers.submittedWhere);
}

export function resolveStuckProblemLabel(answers: QuizAnswers): string | null {
  return pickLabel(stuckProblemOptions, answers.stuckProblemType);
}

export function resolveStuckSubmittedItems(answers: QuizAnswers): string | null {
  const ids = answers.stuckSubmittedItems;
  if (!ids?.length) return null;
  return ids
    .map((id) => stuckSubmittedItemOptions.find((o) => o.id === id)?.label ?? id)
    .join("; ");
}

export function resolveStuckSubmittedToList(answers: QuizAnswers): string | null {
  const ids = answers.stuckSubmittedToList;
  if (!ids?.length) return null;
  return ids
    .map((id) => stuckSubmittedToOptions.find((o) => o.id === id)?.label ?? id)
    .join("; ");
}
