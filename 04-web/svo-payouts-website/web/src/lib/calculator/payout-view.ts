import { findRegionCatalogEntry } from "@/data/regions/catalog";
import { isFreshQuizComplete } from "@/lib/calculator/fresh-payout-calculator";
import { buildFreshPayoutBreakdownView } from "@/lib/calculator/fresh-payout-view";
import type { PayoutBreakdownView, RegionalCatalogStatus } from "@/types/payouts";
import type { QuizAnswers } from "@/types/quiz";
import { AMOUNTS, showsChildMonthlyNote } from "@/lib/calculator";

function federalLines() {
  return [
    {
      id: "presidential",
      title: "Президентская выплата",
      amountRub: AMOUNTS.presidentialPayment,
    },
    {
      id: "benefit306",
      title: "Единовременное пособие по 306-ФЗ",
      amountRub: AMOUNTS.benefit306Fz,
    },
    {
      id: "insurance",
      title: "Страховая / компенсационная выплата",
      amountRub: AMOUNTS.insurancePayment,
    },
  ];
}

function monthlyLinesForAnswers(answers: QuizAnswers) {
  const lines: PayoutBreakdownView["monthlyLines"] = [];
  const child = showsChildMonthlyNote(answers.relation);
  if (child) {
    lines.push({
      id: "child_monthly",
      title: "Ежемесячное пособие детям",
      amountRub: AMOUNTS.childMonthlyPayment,
      description:
        "Ориентир на одного ребёнка при соответствующем статусу; точный состав и продолжительность зависят от документов и решений.",
    });
  }
  lines.push({
    id: "monthly_other",
    title: "Иные ежемесячные выплаты и пенсия по потере кормильца",
    amountRub: null,
    description:
      "Зависят от статуса, стажа, возраста и региона — требуют отдельного разбора, на экране не суммируются с разовыми федеральными выплатами.",
  });
  return lines;
}

function otherMeasures(): PayoutBreakdownView["otherMeasures"] {
  return [
    {
      id: "burial",
      title: "Погребение и ритуальные расходы",
      description:
        "Могут дополнительно применяться, уточняются после анализа документов, региона и ведомства.",
    },
    {
      id: "regional_extra",
      title: "Иные региональные меры",
      description:
        "Зависят от субъекта РФ и категории — см. блок «Региональные выплаты» или отдельную проверку.",
    },
    {
      id: "status_based",
      title: "Компенсации, зависящие от ведомства и статуса",
      description:
        "Не унифицированы в этом расчёте; оцениваются по вашему кейсу отдельно.",
    },
  ];
}

export function buildLegacyPayoutBreakdownView(answers: QuizAnswers): PayoutBreakdownView {
  const federalOneTimeLines = federalLines();
  const federalOneTimeTotal = federalOneTimeLines.reduce((s, x) => s + x.amountRub, 0);

  const regionText = (answers.region ?? "").trim();
  const entry = regionText.length >= 2 ? findRegionCatalogEntry(regionText) : null;

  let regionalLines: PayoutBreakdownView["regional"]["lines"] = [];
  let catalogIncomplete = false;
  let disclaimer: string | null = null;
  let needsManualCheck = false;

  if (!entry) {
    needsManualCheck = regionText.length >= 2;
  } else {
    catalogIncomplete = Boolean(entry.catalogNote);
    disclaimer = entry.catalogNote;
    regionalLines = entry.payments.map((p) => ({
      id: p.id,
      title: p.title,
      amountRub: p.amountRub,
      recipientsNote: p.recipients,
      description: p.description,
      isPartial: !p.available || p.amountRub === null,
    }));
    if (regionalLines.length === 0) {
      needsManualCheck = true;
    }
  }

  const regionLenOk = regionText.length >= 2;

  let catalogLastUpdated: string | null = null;
  if (entry?.payments.length) {
    catalogLastUpdated = [...entry.payments]
      .map((p) => p.lastUpdated)
      .sort()
      .at(-1) ?? null;
  }

  let blockStatus: RegionalCatalogStatus;
  if (!regionLenOk) {
    blockStatus = "no_data";
  } else if (!entry || (regionalLines.length === 0 && needsManualCheck)) {
    blockStatus = "needs_verification";
  } else if (catalogIncomplete || regionalLines.some((l) => l.isPartial)) {
    blockStatus = "partial";
  } else {
    blockStatus = "confirmed";
  }

  return {
    federalOneTimeLines,
    federalOneTimeTotal,
    monthlyLines: monthlyLinesForAnswers(answers),
    regional: {
      regionName: entry?.name ?? null,
      regionCode: entry?.code ?? null,
      lines: regionalLines,
      catalogIncomplete,
      needsManualCheck,
      disclaimer,
      blockStatus,
      catalogLastUpdated,
    },
    otherMeasures: otherMeasures(),
  };
}

/** Предрасчёт: новый квиз fresh или устаревшая цепочка. */
export function buildPayoutBreakdownView(answers: QuizAnswers): PayoutBreakdownView {
  if (isFreshQuizComplete(answers)) {
    return buildFreshPayoutBreakdownView(answers);
  }
  return buildLegacyPayoutBreakdownView(answers);
}

/** Сумма трёх федеральных разовых строк для заголовка и доли (без региональных и ежемесячных). */
export function federalTotalForHeadline(): number {
  return AMOUNTS.presidentialPayment + AMOUNTS.benefit306Fz + AMOUNTS.insurancePayment;
}
