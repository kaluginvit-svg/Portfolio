import type { QuizAnswers } from "@/types/quiz";

/** Старый квиз fresh (до замены на 8 шагов) — для API и сохранённых ответов. */
export function isLegacyFreshQuizComplete(a: QuizAnswers): boolean {
  const regionOk = (a.region ?? "").trim().length >= 2;
  const docs = a.documents;
  return (
    a.deceasedRole != null &&
    a.relation != null &&
    (a.relation !== "complex" || a.relationComplexSub != null) &&
    a.recipients != null &&
    (a.recipients !== "me_plus_4_or_more" || a.recipientsExact != null) &&
    Array.isArray(docs) &&
    docs.length > 0 &&
    regionOk
  );
}
