import { describe, expect, it } from "vitest";
import {
  computeFreshPayoutCalculation,
  FRESH_AMOUNTS,
  isFreshQuizComplete,
} from "@/lib/calculator/fresh-payout-calculator";
import type { QuizAnswers } from "@/types/quiz";

function baseFreshAnswers(over: Partial<QuizAnswers> = {}): QuizAnswers {
  return {
    serviceStatus: "contract_mobilized",
    freshApplicantRole: "spouse_registered",
    freshRecipientsCount: "1",
    freshChildrenCount: "0",
    deathBasis: "duty",
    ambiguityFlag: "no",
    region: "Москва",
    calcMode: "federal_only",
    ...over,
  };
}

describe("isFreshQuizComplete", () => {
  it("false при пустых ответах", () => {
    expect(isFreshQuizComplete({})).toBe(false);
  });

  it("false если регион короче 2 символов", () => {
    expect(isFreshQuizComplete(baseFreshAnswers({ region: "М" }))).toBe(false);
  });

  it("true при полном снимке", () => {
    expect(isFreshQuizComplete(baseFreshAnswers())).toBe(true);
  });
});

describe("computeFreshPayoutCalculation", () => {
  it("null если квиз неполный", () => {
    expect(computeFreshPayoutCalculation({})).toBeNull();
  });

  it("standard: полный пакет, preliminary_ok, доля = lump / получателей", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({ freshRecipientsCount: "3" }),
    );
    expect(calc).not.toBeNull();
    expect(calc!.branch).toBe("standard");
    expect(calc!.lumpSumTotal).toBeCloseTo(FRESH_AMOUNTS.baseLumpStandard, 5);
    expect(calc!.includesInsurance52).toBe(true);
    expect(calc!.headlineMode).toBe("none");
    expect(calc!.precision).toBe("preliminary_ok");
    expect(calc!.personalShareRub).toBeCloseTo(FRESH_AMOUNTS.baseLumpStandard / 3, 3);
    expect(calc!.consultant.consultant_breakdown_insurance_52).toBe(FRESH_AMOUNTS.insurance52);
    expect(calc!.consultant.consultant_personal_share).toMatch(/\d/);
    expect(calc!.clarificationNote).toBeNull();
    expect(calc!.regionalNote).toBeNull();
  });

  it("conservative: доброволец, от страховки 0, headline «от»", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({
        serviceStatus: "volunteer",
        freshRecipientsCount: "2",
      }),
    );
    expect(calc!.branch).toBe("conservative");
    expect(calc!.lumpSumTotal).toBeCloseTo(FRESH_AMOUNTS.baseLumpConservative, 5);
    expect(calc!.includesInsurance52).toBe(false);
    expect(calc!.headlineMode).toBe("from");
    expect(calc!.precision).toBe("needs_clarification");
    expect(calc!.consultant.consultant_breakdown_insurance_52).toBe(0);
    expect(calc!.headlineAmountDisplay.startsWith("от ")).toBe(true);
  });

  it("disputed + стандартная база: «до», lump стандартный", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({ ambiguityFlag: "yes" }),
    );
    expect(calc!.branch).toBe("disputed_standard");
    expect(calc!.headlineMode).toBe("up_to");
    expect(calc!.lumpSumTotal).toBeCloseTo(FRESH_AMOUNTS.baseLumpStandard, 5);
    expect(calc!.precision).toBe("needs_clarification");
    expect(calc!.headlineAmountDisplay.startsWith("до ")).toBe(true);
  });

  it("disputed + нестандартный статус службы: conservative lump и «от»", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({
        serviceStatus: "volunteer",
        ambiguityFlag: "yes",
      }),
    );
    expect(calc!.branch).toBe("disputed_conservative");
    expect(calc!.lumpSumTotal).toBeCloseTo(FRESH_AMOUNTS.baseLumpConservative, 5);
    expect(calc!.headlineMode).toBe("from");
  });

  it("disputed + recipients unknown: доля null, строка консультанта", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({
        freshRecipientsCount: "unknown",
        ambiguityFlag: "yes",
      }),
    );
    expect(calc!.personalShareRub).toBeNull();
    expect(calc!.consultant.consultant_personal_share).toBe("требует уточнений");
  });

  it("cohabitation_no_marriage ведёт в disputed", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({
        freshApplicantRole: "cohabitation_no_marriage",
        ambiguityFlag: "no",
      }),
    );
    expect(calc!.branch).toBe("disputed_standard");
    expect(calc!.precision).toBe("needs_clarification");
  });

  it("death_basis disease: пенсия на ребёнка снижена", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({
        freshChildrenCount: "1",
        deathBasis: "disease",
      }),
    );
    expect(calc!.pensionPerChildUsed).toBe(FRESH_AMOUNTS.childPensionDisease);
    expect(calc!.monthlyPensionPart).toBeCloseTo(FRESH_AMOUNTS.childPensionDisease, 5);
    expect(calc!.monthlyAllowancePart).toBeCloseTo(FRESH_AMOUNTS.childMonthlyAllowancePerChild, 5);
    expect(calc!.monthlyChildrenTotal).toBeCloseTo(
      FRESH_AMOUNTS.childMonthlyAllowancePerChild + FRESH_AMOUNTS.childPensionDisease,
      5,
    );
  });

  it("death_basis unknown + дети: верхняя ставка пенсии и флаг неопределённости", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({
        freshChildrenCount: "2",
        deathBasis: "unknown",
      }),
    );
    expect(calc!.pensionPerChildUsed).toBe(FRESH_AMOUNTS.childPensionDuty);
    expect(calc!.deathBasisPensionUncertain).toBe(true);
    expect(calc!.precision).toBe("needs_clarification");
  });

  it("дети 0: ежемесячный блок 0", () => {
    const calc = computeFreshPayoutCalculation(baseFreshAnswers({ freshChildrenCount: "0" }));
    expect(calc!.monthlyChildrenTotal).toBe(0);
    expect(calc!.consultant.consultant_monthly_children_total).toBe("0,00 ₽/мес");
  });

  it("3_plus детей: в расчёте три ребёнка", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({
        freshChildrenCount: "3_plus",
        deathBasis: "duty",
      }),
    );
    expect(calc!.childrenNumeric).toBe(3);
    const perChild =
      FRESH_AMOUNTS.childMonthlyAllowancePerChild + FRESH_AMOUNTS.childPensionDuty;
    expect(calc!.monthlyChildrenTotal).toBeCloseTo(perChild * 3, 5);
  });

  it("federal_plus_region: regionalNote и breakdown note", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({ calcMode: "federal_plus_region" }),
    );
    expect(calc!.regionalNote).toContain("Региональные выплаты");
    expect(calc!.consultant.consultant_breakdown_region_note).toContain("не включены");
  });

  it("radiation stub в consultant", () => {
    const calc = computeFreshPayoutCalculation(baseFreshAnswers());
    expect(calc!.consultant.radiation_module_status).toBe("not_included");
    expect(calc!.consultant.radiation_module_note.length).toBeGreaterThan(10);
  });

  it("consultant_summary содержит ключевые части", () => {
    const calc = computeFreshPayoutCalculation(
      baseFreshAnswers({ freshRecipientsCount: "3" }),
    );
    const s = calc!.consultant.consultant_summary;
    expect(s).toContain("Итоговый ориентировочный федеральный расчёт");
    expect(s).toContain("Разовые выплаты семье");
    expect(s).toContain("Ориентировочная доля заявителя");
    expect(s).toContain("Ежемесячно на детей");
    expect(s).toContain("Статус расчёта");
  });

  it("raw_answers содержит ключи нового квиза", () => {
    const a = baseFreshAnswers({ region: " Казань " });
    const calc = computeFreshPayoutCalculation(a);
    expect(calc!.consultant.raw_answers.serviceStatus).toBe("contract_mobilized");
    expect(calc!.consultant.raw_answers.region).toBe("Казань");
  });
});
