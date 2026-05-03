import type { QuizAnswers, Relation, WaitingOption } from "@/types/quiz";

export const AMOUNTS = {
  presidentialPayment: 5_000_000,
  benefit306Fz: 5_524_892.57,
  insurancePayment: 3_683_261.71,
  childMonthlyPayment: 3_311.15,
  baseTotal: 14_208_154.28,
} as const;

const WAITING_TO_MONTHS: Record<WaitingOption, number> = {
  lt1m: 1,
  "1to3m": 2,
  "3to6m": 4,
  gt6m: 6,
};

export function getRecipientsCount(answers: QuizAnswers): number {
  if (answers.serviceStatus != null && answers.freshRecipientsCount != null) {
    const r = answers.freshRecipientsCount;
    if (r === "unknown") return 1;
    if (r === "5_plus") return 5;
    const n = Number(r);
    return Number.isFinite(n) && n > 0 ? n : 1;
  }
  switch (answers.recipients) {
    case "only_me":
      return 1;
    case "me_plus_1":
      return 2;
    case "me_plus_2":
      return 3;
    case "me_plus_3":
      return 4;
    case "me_plus_4_or_more": {
      switch (answers.recipientsExact) {
        case "4":
          return 4;
        case "5":
          return 5;
        case "6":
          return 6;
        case "7_plus":
          return 7;
        default:
          return 4;
      }
    }
    default:
      return 1;
  }
}

export function getWaitingMonths(waiting: WaitingOption | undefined): number {
  if (!waiting) return 0;
  return WAITING_TO_MONTHS[waiting];
}

export function showsChildMonthlyNote(relation: Relation | undefined): boolean {
  return relation === "child_under_18" || relation === "child_student";
}

export function formatRub(value: number): string {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/** Число с пробелами по разрядам — для крупной типографики (символ ₽ отдельно). */
export function formatRubAmount(value: number): string {
  return new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}
