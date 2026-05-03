import { formatRub, formatRubAmount } from "@/lib/calculator";
import type {
  AmbiguityFlag,
  CalcMode,
  DeathBasis,
  FreshApplicantRole,
  FreshChildrenCount,
  FreshRecipientsCount,
  QuizAnswers,
  ServiceStatus,
} from "@/types/quiz";

/** Базовые величины (федеральный ориентир). */
export const FRESH_AMOUNTS = {
  presidentPayment: 5_000_000,
  lump306: 5_524_892.57,
  insurance52: 3_683_261.71,
  baseLumpStandard: 14_208_154.28,
  baseLumpConservative: 10_524_892.57,
  childMonthlyAllowancePerChild: 3_311.15,
  childPensionDuty: 15_379.66,
  childPensionDisease: 11_534.75,
} as const;

export type FreshPrecision = "preliminary_ok" | "needs_clarification";
export type FreshHeadlineMode = "none" | "up_to" | "from";

export interface FreshPayoutCalculation {
  branch: "standard" | "conservative" | "disputed_standard" | "disputed_conservative";
  lumpSumTotal: number;
  includesInsurance52: boolean;
  headlineMode: FreshHeadlineMode;
  headlineAmountNumeric: number;
  headlinePrefix: string;
  headlineAmountDisplay: string;
  personalShareRub: number | null;
  recipientsNumeric: number | null;
  childrenNumeric: number;
  monthlyAllowancePart: number;
  monthlyPensionPart: number;
  monthlyChildrenTotal: number;
  pensionPerChildUsed: number;
  deathBasisPensionUncertain: boolean;
  precision: FreshPrecision;
  precisionLabel: string;
  clarificationNote: string | null;
  regionalNote: string | null;
  radiationModuleStatus: "not_included";
  radiationModuleNote: string;
  /** Поля для вебхука / консультанта */
  consultant: FreshConsultantPayloadFields;
}

export interface FreshConsultantPayloadFields {
  raw_answers: Record<string, string | undefined>;
  consultant_total_amount: string;
  consultant_total_amount_label: string;
  consultant_lump_sum_total: string;
  consultant_personal_share: string;
  consultant_monthly_children_total: string;
  consultant_monthly_allowance_part: string;
  consultant_monthly_pension_part: string;
  consultant_precision_label: string;
  consultant_summary: string;
  service_status: ServiceStatus | undefined;
  applicant_role: FreshApplicantRole | undefined;
  recipients_count: FreshRecipientsCount | undefined;
  children_count: FreshChildrenCount | undefined;
  death_basis: DeathBasis | undefined;
  ambiguity_flag: AmbiguityFlag | undefined;
  region: string | undefined;
  calc_mode: CalcMode | undefined;
  consultant_breakdown_lump_sum: string;
  consultant_breakdown_president_payment: number;
  consultant_breakdown_306_payment: number;
  consultant_breakdown_insurance_52: number;
  consultant_breakdown_monthly_child_allowance: number;
  consultant_breakdown_monthly_child_pension: number;
  consultant_breakdown_region_included: boolean;
  consultant_breakdown_region_note: string;
  radiation_module_status: string;
  radiation_module_note: string;
}

function recipientsToNumber(r: FreshRecipientsCount | undefined): number | null {
  if (r == null) return null;
  if (r === "unknown") return null;
  if (r === "5_plus") return 5;
  return Number(r);
}

function childrenToNumber(c: FreshChildrenCount | undefined): number {
  if (c == null) return 0;
  if (c === "3_plus") return 3;
  return Number(c);
}

function isStandardService(s: ServiceStatus | undefined): boolean {
  return s === "contract_mobilized" || s === "force_department";
}

function isConservativeService(s: ServiceStatus | undefined): boolean {
  return s === "volunteer" || s === "unknown";
}

function isDisputedTrigger(a: QuizAnswers): boolean {
  if (a.ambiguityFlag === "yes" || a.ambiguityFlag === "unknown") return true;
  if (a.freshApplicantRole === "cohabitation_no_marriage") return true;
  if (a.freshRecipientsCount === "unknown") return true;
  return false;
}

function monthlyPrefix(precision: FreshPrecision, hasChildren: boolean): string {
  if (!hasChildren) return "";
  return precision === "needs_clarification" ? "до " : "";
}

function buildConsultantSummary(p: {
  headlineAmountForText: string;
  lumpStr: string;
  shareStr: string;
  monthlyStr: string;
  precisionLower: string;
  clarification: string | null;
}): string {
  const tail = p.clarification ? ` ${p.clarification}` : "";
  return `Итоговый ориентировочный федеральный расчёт: ${p.headlineAmountForText}. Разовые выплаты семье: ${p.lumpStr}. Ориентировочная доля заявителя: ${p.shareStr}. Ежемесячно на детей: ${p.monthlyStr}. Статус расчёта: ${p.precisionLower}.${tail}`;
}

export function isFreshQuizComplete(a: QuizAnswers): boolean {
  const regionOk = (a.region ?? "").trim().length >= 2;
  return (
    a.serviceStatus != null &&
    a.freshApplicantRole != null &&
    a.freshRecipientsCount != null &&
    a.freshChildrenCount != null &&
    a.deathBasis != null &&
    a.ambiguityFlag != null &&
    a.calcMode != null &&
    regionOk
  );
}

export function computeFreshPayoutCalculation(a: QuizAnswers): FreshPayoutCalculation | null {
  if (!isFreshQuizComplete(a)) return null;

  const recipientsN = recipientsToNumber(a.freshRecipientsCount);
  const childrenN = childrenToNumber(a.freshChildrenCount);
  const disputed = isDisputedTrigger(a);

  let lumpSum: number;
  let includesInsurance: boolean;
  let headlineMode: FreshHeadlineMode;
  let branch: FreshPayoutCalculation["branch"];

  if (disputed) {
    if (isStandardService(a.serviceStatus)) {
      lumpSum = FRESH_AMOUNTS.baseLumpStandard;
      includesInsurance = true;
      headlineMode = "up_to";
      branch = "disputed_standard";
    } else {
      lumpSum = FRESH_AMOUNTS.baseLumpConservative;
      includesInsurance = false;
      headlineMode = "from";
      branch = "disputed_conservative";
    }
  } else if (isConservativeService(a.serviceStatus)) {
    lumpSum = FRESH_AMOUNTS.baseLumpConservative;
    includesInsurance = false;
    headlineMode = "from";
    branch = "conservative";
  } else {
    lumpSum = FRESH_AMOUNTS.baseLumpStandard;
    includesInsurance = true;
    headlineMode = "none";
    branch = "standard";
  }

  let personalShare: number | null =
    recipientsN != null && recipientsN > 0 ? lumpSum / recipientsN : null;
  if (disputed && a.freshRecipientsCount === "unknown") {
    personalShare = null;
  }
  if (!disputed && isConservativeService(a.serviceStatus) && recipientsN == null) {
    personalShare = null;
  }

  let pensionPerChild =
    a.deathBasis === "disease"
      ? FRESH_AMOUNTS.childPensionDisease
      : FRESH_AMOUNTS.childPensionDuty;
  let deathBasisPensionUncertain = false;
  if (a.deathBasis === "unknown") {
    pensionPerChild = FRESH_AMOUNTS.childPensionDuty;
    deathBasisPensionUncertain = childrenN > 0;
  }

  const monthlyAllowance = FRESH_AMOUNTS.childMonthlyAllowancePerChild * childrenN;
  const monthlyPension = pensionPerChild * childrenN;
  const monthlyTotal = monthlyAllowance + monthlyPension;

  let precision: FreshPrecision = "preliminary_ok";
  if (disputed || isConservativeService(a.serviceStatus)) {
    precision = "needs_clarification";
  }
  if (deathBasisPensionUncertain) {
    precision = "needs_clarification";
  }

  const precisionLabel =
    precision === "preliminary_ok" ? "Предварительный расчёт" : "Требует уточнений";

  const clarificationNote =
    precision === "needs_clarification"
      ? "Сумма рассчитана по наиболее вероятному федеральному сценарию и требует уточнений."
      : null;

  let regionalNote: string | null = null;
  if (a.calcMode === "federal_plus_region" || a.calcMode === "unknown") {
    regionalNote =
      "Региональные выплаты не включены в автоматический расчёт и требуют отдельной проверки.";
  }

  const radiationModuleStatus = "not_included" as const;
  const radiationModuleNote =
    "Дополнительный модуль по радиационным/техногенным основаниям не включён в автоматический расчёт.";

  const headlineAmountNumeric = lumpSum;
  const amountFmt = `${formatRubAmount(headlineAmountNumeric)} ₽`;
  const headlinePrefix = "Ваш ориентировочный федеральный расчёт";
  let headlineAmountDisplay: string;
  if (headlineMode === "up_to") headlineAmountDisplay = `до ${amountFmt}`;
  else if (headlineMode === "from") headlineAmountDisplay = `от ${amountFmt}`;
  else headlineAmountDisplay = amountFmt;

  const lumpStr = formatRub(lumpSum);
  const shareStr =
    personalShare != null ? formatRub(personalShare) : "требует уточнений";
  const mPrefix = monthlyPrefix(precision, childrenN > 0);
  const monthlyStr =
    childrenN === 0
      ? "0,00 ₽/мес"
      : `${mPrefix}${formatRubAmount(monthlyTotal)} ₽/мес`;

  const precisionLower =
    precision === "preliminary_ok" ? "предварительный" : "требует уточнений";
  const clarificationForSummary =
    precision === "needs_clarification" ? clarificationNote?.replace(/\.$/, "") : null;

  const consultant_total_amount = headlineAmountDisplay;
  const consultant_total_amount_label = headlinePrefix;

  const raw_answers: Record<string, string | undefined> = {
    serviceStatus: a.serviceStatus,
    freshApplicantRole: a.freshApplicantRole,
    freshRecipientsCount: a.freshRecipientsCount,
    freshChildrenCount: a.freshChildrenCount,
    deathBasis: a.deathBasis,
    ambiguityFlag: a.ambiguityFlag,
    calcMode: a.calcMode,
    region: a.region?.trim(),
  };

  const insuranceBreakdown = includesInsurance ? FRESH_AMOUNTS.insurance52 : 0;

  const consultant: FreshConsultantPayloadFields = {
    raw_answers,
    consultant_total_amount,
    consultant_total_amount_label,
    consultant_lump_sum_total: lumpStr,
    consultant_personal_share: shareStr,
    consultant_monthly_children_total:
      childrenN === 0 ? "0,00 ₽/мес" : `${mPrefix}${formatRubAmount(monthlyTotal)} ₽/мес`,
    consultant_monthly_allowance_part: formatRub(monthlyAllowance),
    consultant_monthly_pension_part: formatRub(monthlyPension),
    consultant_precision_label: precisionLabel,
    consultant_summary: buildConsultantSummary({
      headlineAmountForText: headlineAmountDisplay,
      lumpStr,
      shareStr,
      monthlyStr,
      precisionLower,
      clarification: clarificationForSummary ?? null,
    }),
    service_status: a.serviceStatus,
    applicant_role: a.freshApplicantRole,
    recipients_count: a.freshRecipientsCount,
    children_count: a.freshChildrenCount,
    death_basis: a.deathBasis,
    ambiguity_flag: a.ambiguityFlag,
    region: a.region?.trim(),
    calc_mode: a.calcMode,
    consultant_breakdown_lump_sum: lumpStr,
    consultant_breakdown_president_payment: FRESH_AMOUNTS.presidentPayment,
    consultant_breakdown_306_payment: FRESH_AMOUNTS.lump306,
    consultant_breakdown_insurance_52: insuranceBreakdown,
    consultant_breakdown_monthly_child_allowance: monthlyAllowance,
    consultant_breakdown_monthly_child_pension: monthlyPension,
    consultant_breakdown_region_included: false,
    consultant_breakdown_region_note:
      a.calcMode === "federal_plus_region" || a.calcMode === "unknown"
        ? "Региональные выплаты не включены в автоматический расчёт и требуют отдельной проверки."
        : "Региональные выплаты в автоматический расчёт не включены.",
    radiation_module_status: radiationModuleStatus,
    radiation_module_note: radiationModuleNote,
  };

  return {
    branch,
    lumpSumTotal: lumpSum,
    includesInsurance52: includesInsurance,
    headlineMode,
    headlineAmountNumeric,
    headlinePrefix,
    headlineAmountDisplay,
    personalShareRub: personalShare,
    recipientsNumeric: recipientsN,
    childrenNumeric: childrenN,
    monthlyAllowancePart: monthlyAllowance,
    monthlyPensionPart: monthlyPension,
    monthlyChildrenTotal: monthlyTotal,
    pensionPerChildUsed: pensionPerChild,
    deathBasisPensionUncertain,
    precision,
    precisionLabel,
    clarificationNote,
    regionalNote,
    radiationModuleStatus,
    radiationModuleNote,
    consultant,
  };
}
