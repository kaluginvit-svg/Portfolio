import { findRegionCatalogEntry } from "@/data/regions/catalog";
import { formatRub } from "@/lib/calculator";
import {
  computeFreshPayoutCalculation,
  FRESH_AMOUNTS,
} from "@/lib/calculator/fresh-payout-calculator";
import type { PayoutBreakdownView } from "@/types/payouts";
import type { QuizAnswers } from "@/types/quiz";

/** Мета для экрана результата (новый квиз) — те же классы/разметка, другие строки и числа. */
export function buildFreshPayoutBreakdownView(answers: QuizAnswers): PayoutBreakdownView {
  const calc = computeFreshPayoutCalculation(answers);
  if (!calc) {
    throw new Error("buildFreshPayoutBreakdownView: неполные ответы");
  }

  const federalOneTimeLines = [
    {
      id: "presidential",
      title: "Президентская выплата",
      amountRub: FRESH_AMOUNTS.presidentPayment,
    },
    {
      id: "benefit306",
      title: "Единовременное пособие по 306-ФЗ",
      amountRub: FRESH_AMOUNTS.lump306,
    },
    {
      id: "insurance",
      title: "Страховая / компенсационная выплата",
      amountRub: calc.includesInsurance52 ? FRESH_AMOUNTS.insurance52 : 0,
    },
  ];

  const monthlyLines: PayoutBreakdownView["monthlyLines"] = [];
  if (calc.childrenNumeric === 0) {
    monthlyLines.push({
      id: "child_allowance",
      title: "Ежемесячное пособие на детей (в расчёте)",
      amountRub: 0,
      description:
        "В опросе указано, что детей для ежемесячного блока нет — сумма 0 ₽/мес.",
    });
    monthlyLines.push({
      id: "child_pension",
      title: "Ежемесячная пенсия по потере кормильца (дети)",
      amountRub: 0,
      description: "Не суммируется с разовыми федеральными выплатами в одну строку сверху.",
    });
  } else {
    monthlyLines.push({
      id: "child_allowance",
      title: "Ежемесячное пособие на детей",
      amountRub: calc.monthlyAllowancePart,
      description: `Ориентир на ${calc.childrenNumeric} ${childWord(calc.childrenNumeric)}: ${formatRub(FRESH_AMOUNTS.childMonthlyAllowancePerChild)} на каждого.`,
    });
    monthlyLines.push({
      id: "child_pension",
      title: "Ежемесячная пенсия детям",
      amountRub: calc.monthlyPensionPart,
      description:
        calc.deathBasisPensionUncertain
          ? "База пенсии взята по верхнему ориентиру до уточнения причины смерти; итог помечен как требующий уточнений."
          : "Сумма на всех детей в расчёте; точные основания зависят от документов.",
    });
    monthlyLines.push({
      id: "child_monthly_total",
      title: "Итого ежемесячный детский блок",
      amountRub: calc.monthlyChildrenTotal,
      description: "Пособие и пенсия по детям вместе; не входит в крупную разовую сумму сверху.",
    });
  }

  const otherMeasures: PayoutBreakdownView["otherMeasures"] = [
    {
      id: "radiation_stub",
      title: "Радиационные / техногенные основания",
      description: calc.radiationModuleNote,
    },
    {
      id: "burial",
      title: "Погребение и ритуальные расходы",
      description:
        "Могут дополнительно применяться, уточняются после анализа документов, региона и ведомства.",
    },
    {
      id: "adult_pension",
      title: "Пенсии взрослым получателям",
      description:
        "Взрослые пенсии супругу / родителям в автоматический расчёт не включены — требуют отдельного разбора.",
    },
  ];

  const regionText = (answers.region ?? "").trim();
  const entry = regionText.length >= 2 ? findRegionCatalogEntry(regionText) : null;

  return {
    federalOneTimeLines,
    federalOneTimeTotal: calc.lumpSumTotal,
    monthlyLines,
    regional: {
      regionName: entry?.name ?? (regionText.length >= 2 ? regionText : null),
      regionCode: entry?.code ?? null,
      lines: [],
      catalogIncomplete: true,
      needsManualCheck: true,
      /** Текст про регион из calc уже в `freshMeta.regionalNote` под заголовком — не дублируем в карточке. */
      disclaimer: null,
      blockStatus: "needs_verification",
      catalogLastUpdated: null,
    },
    otherMeasures,
    freshMeta: {
      headlinePrefix: calc.headlinePrefix,
      headlineAmountNumeric: calc.headlineAmountNumeric,
      headlineMode: calc.headlineMode,
      headlineAmountDisplay: calc.headlineAmountDisplay,
      precisionLabel: calc.precisionLabel,
      clarificationNote: calc.clarificationNote,
      regionalNote: calc.regionalNote,
      radiationModuleNote: calc.radiationModuleNote,
      personalShareRub: calc.personalShareRub,
      monthlyChildrenTotal: calc.monthlyChildrenTotal,
      monthlyAllowancePart: calc.monthlyAllowancePart,
      monthlyPensionPart: calc.monthlyPensionPart,
      shareRequiresClarification: calc.personalShareRub == null,
      monthlyPrefix:
        calc.childrenNumeric > 0 && calc.precision === "needs_clarification" ? "до " : "",
    },
  };
}

function childWord(n: number): string {
  if (n === 1) return "ребёнка";
  if (n >= 2 && n <= 4) return "детей";
  return "детей";
}
