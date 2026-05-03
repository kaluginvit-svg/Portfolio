import { describe, expect, it } from "vitest";
import { AMOUNTS } from "@/lib/calculator";
import { FRESH_AMOUNTS } from "@/lib/calculator/fresh-payout-calculator";
import {
  buildPayoutBreakdownView,
  federalTotalForHeadline,
} from "@/lib/calculator/payout-view";
import type { QuizAnswers } from "@/types/quiz";

const minimalFreshAnswers = (region: string): QuizAnswers => ({
  deceasedRole: "mobilized",
  relation: "spouse",
  recipients: "only_me",
  documents: ["death_cert"],
  region,
});

describe("buildPayoutBreakdownView (integration)", () => {
  it("федеральный блок и total совпадают с суммой строк", () => {
    const view = buildPayoutBreakdownView(minimalFreshAnswers("Москва"));
    const sumLines = view.federalOneTimeLines.reduce((s, l) => s + l.amountRub, 0);
    expect(view.federalOneTimeTotal).toBeCloseTo(sumLines, 5);
    expect(view.federalOneTimeTotal).toBeCloseTo(AMOUNTS.baseTotal, 5);
  });

  it("СПб: в каталоге есть примечание → блок partial, строка с суммой не помечена как частичная", () => {
    const view = buildPayoutBreakdownView(minimalFreshAnswers("Санкт-Петербург"));
    expect(view.regional.blockStatus).toBe("partial");
    expect(view.regional.catalogIncomplete).toBe(true);
    expect(view.regional.regionName).toBe("Санкт-Петербург");
    expect(view.regional.lines.length).toBeGreaterThan(0);
    expect(view.regional.lines[0].amountRub).toBe(100_000);
    expect(view.regional.lines[0].isPartial).toBe(false);
  });

  it("Москва: каталог с примечанием → partial / неполные суммы", () => {
    const view = buildPayoutBreakdownView(minimalFreshAnswers("Москва"));
    expect(view.regional.blockStatus).toBe("partial");
    expect(view.regional.lines.every((l) => l.isPartial)).toBe(true);
  });

  it("пустой регион → no_data", () => {
    const view = buildPayoutBreakdownView({ ...minimalFreshAnswers(""), region: "" });
    expect(view.regional.blockStatus).toBe("no_data");
    expect(view.regional.lines).toHaveLength(0);
  });

  it("неизвестный длинный регион → needs_verification", () => {
    const view = buildPayoutBreakdownView(
      minimalFreshAnswers("ZZZQQQНесуществующийСубъект999"),
    );
    expect(view.regional.blockStatus).toBe("needs_verification");
    expect(view.regional.needsManualCheck).toBe(true);
  });

  it("ребёнок → строка ежемесячного пособия в monthlyLines", () => {
    const view = buildPayoutBreakdownView({
      ...minimalFreshAnswers("Москва"),
      relation: "child_under_18",
    });
    expect(view.monthlyLines.some((l) => l.id === "child_monthly")).toBe(true);
  });

  it("federalTotalForHeadline совпадает с federalOneTimeTotal", () => {
    expect(federalTotalForHeadline()).toBe(
      buildPayoutBreakdownView(minimalFreshAnswers("Москва")).federalOneTimeTotal,
    );
  });
});

const completeNewFreshQuiz = (over: Partial<QuizAnswers> = {}): QuizAnswers => ({
  serviceStatus: "contract_mobilized",
  freshApplicantRole: "spouse_registered",
  freshRecipientsCount: "1",
  freshChildrenCount: "0",
  deathBasis: "duty",
  ambiguityFlag: "no",
  region: "Москва",
  calcMode: "federal_only",
  ...over,
});

describe("buildPayoutBreakdownView — новый квиз (8 шагов)", () => {
  it("freshMeta и federal total по FRESH_AMOUNTS", () => {
    const view = buildPayoutBreakdownView(completeNewFreshQuiz());
    expect(view.freshMeta).toBeDefined();
    expect(view.federalOneTimeTotal).toBeCloseTo(FRESH_AMOUNTS.baseLumpStandard, 5);
    const sumLines = view.federalOneTimeLines.reduce((s, l) => s + l.amountRub, 0);
    expect(view.federalOneTimeTotal).toBeCloseTo(sumLines, 5);
    expect(view.freshMeta!.headlinePrefix).toContain("ориентировочный");
    expect(view.freshMeta!.precisionLabel).toBe("Предварительный расчёт");
  });

  it("консервативная ветка: страховая строка 0 ₽", () => {
    const view = buildPayoutBreakdownView(
      completeNewFreshQuiz({ serviceStatus: "volunteer" }),
    );
    expect(view.federalOneTimeTotal).toBeCloseTo(FRESH_AMOUNTS.baseLumpConservative, 5);
    const ins = view.federalOneTimeLines.find((l) => l.id === "insurance");
    expect(ins?.amountRub).toBe(0);
    expect(view.freshMeta!.headlineMode).toBe("from");
  });

  it("дети: три строки ежемесячного блока включая итог", () => {
    const view = buildPayoutBreakdownView(
      completeNewFreshQuiz({ freshChildrenCount: "1" }),
    );
    expect(view.monthlyLines.some((l) => l.id === "child_allowance")).toBe(true);
    expect(view.monthlyLines.some((l) => l.id === "child_pension")).toBe(true);
    expect(view.monthlyLines.some((l) => l.id === "child_monthly_total")).toBe(true);
  });

  it("региональный disclaimer не дублируется в карточке (null)", () => {
    const view = buildPayoutBreakdownView(
      completeNewFreshQuiz({ calcMode: "federal_plus_region" }),
    );
    expect(view.regional.disclaimer).toBeNull();
    expect(view.freshMeta?.regionalNote).toContain("Региональные выплаты");
  });
});
