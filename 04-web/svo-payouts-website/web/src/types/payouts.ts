/** Одна строка федеральной разовой выплаты (для UI). */
export interface FederalOneTimeLine {
  id: string;
  title: string;
  amountRub: number;
}

export interface MonthlyPayoutLine {
  id: string;
  title: string;
  /** null — только пояснение без суммы */
  amountRub: number | null;
  description: string;
}

export interface RegionalPayoutLine {
  id: string;
  title: string;
  amountRub: number | null;
  recipientsNote: string | null;
  description: string | null;
  /** Данные предварительные / неполные */
  isPartial?: boolean;
}

export interface OtherMeasureLine {
  id: string;
  title: string;
  description: string;
}

/** Статус блока региональных выплат для UI (badge). */
export type RegionalCatalogStatus =
  | "confirmed"
  | "partial"
  | "needs_verification"
  | "no_data";

/** Данные для экрана результата при новом квизе выплат (без смены визуальных компонентов). */
export interface FreshPayoutResultMeta {
  headlinePrefix: string;
  headlineAmountNumeric: number;
  headlineMode: "none" | "up_to" | "from";
  headlineAmountDisplay: string;
  precisionLabel: string;
  clarificationNote: string | null;
  regionalNote: string | null;
  radiationModuleNote: string;
  personalShareRub: number | null;
  monthlyChildrenTotal: number;
  monthlyAllowancePart: number;
  monthlyPensionPart: number;
  shareRequiresClarification: boolean;
  /** Префикс «до » для ежемесячного итога при needs_clarification */
  monthlyPrefix: string;
}

export interface PayoutBreakdownView {
  federalOneTimeLines: FederalOneTimeLine[];
  federalOneTimeTotal: number;
  monthlyLines: MonthlyPayoutLine[];
  /** Заполняется только для нового квиза расчёта выплат */
  freshMeta?: FreshPayoutResultMeta;
  regional: {
    regionName: string | null;
    regionCode: string | null;
    lines: RegionalPayoutLine[];
    catalogIncomplete: boolean;
    /** Нет строк и нет уверенного совпадения региона */
    needsManualCheck: boolean;
    disclaimer: string | null;
    blockStatus: RegionalCatalogStatus;
    /** Макс. lastUpdated по строкам каталога, ISO date string */
    catalogLastUpdated: string | null;
  };
  otherMeasures: OtherMeasureLine[];
}
