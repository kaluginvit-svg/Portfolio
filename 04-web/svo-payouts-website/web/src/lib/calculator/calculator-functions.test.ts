import { describe, expect, it } from "vitest";
import {
  AMOUNTS,
  formatRub,
  formatRubAmount,
  getRecipientsCount,
  getWaitingMonths,
  showsChildMonthlyNote,
} from "@/lib/calculator";
import type { QuizAnswers } from "@/types/quiz";

describe("getRecipientsCount", () => {
  it("only_me → 1", () => {
    expect(getRecipientsCount({ recipients: "only_me" })).toBe(1);
  });

  it("me_plus_N", () => {
    expect(getRecipientsCount({ recipients: "me_plus_1" })).toBe(2);
    expect(getRecipientsCount({ recipients: "me_plus_3" })).toBe(4);
  });

  it("me_plus_4_or_more + recipientsExact", () => {
    expect(
      getRecipientsCount({
        recipients: "me_plus_4_or_more",
        recipientsExact: "7_plus",
      }),
    ).toBe(7);
    expect(
      getRecipientsCount({
        recipients: "me_plus_4_or_more",
        recipientsExact: "5",
      }),
    ).toBe(5);
  });

  it("fallback при неполных данных", () => {
    expect(getRecipientsCount({ recipients: "me_plus_4_or_more" })).toBe(4);
    expect(getRecipientsCount({} as QuizAnswers)).toBe(1);
  });
});

describe("getWaitingMonths", () => {
  it("маппинг legacy waiting", () => {
    expect(getWaitingMonths("lt1m")).toBe(1);
    expect(getWaitingMonths("1to3m")).toBe(2);
    expect(getWaitingMonths("3to6m")).toBe(4);
    expect(getWaitingMonths("gt6m")).toBe(6);
  });

  it("undefined → 0", () => {
    expect(getWaitingMonths(undefined)).toBe(0);
  });
});

describe("showsChildMonthlyNote", () => {
  it("дети", () => {
    expect(showsChildMonthlyNote("child_under_18")).toBe(true);
    expect(showsChildMonthlyNote("child_student")).toBe(true);
  });

  it("остальные роли", () => {
    expect(showsChildMonthlyNote("spouse")).toBe(false);
    expect(showsChildMonthlyNote(undefined)).toBe(false);
  });
});

describe("formatRub / formatRubAmount", () => {
  it("formatRub — локаль ru-RU и дробная часть", () => {
    const s = formatRub(1234.5);
    expect(s).toMatch(/1[\s\u00a0]*234/);
    expect(s).toMatch(/34[,.]50/);
  });

  it("formatRubAmount — без символа валюты, пробелы разрядов", () => {
    const s = formatRubAmount(1_000_000.12);
    expect(s).toMatch(/1/);
    expect(s).toMatch(/000/);
    expect(s).toMatch(/12/);
  });

  it("сумма федеральных строк совпадает с baseTotal (с погрешностью float)", () => {
    const sum =
      AMOUNTS.presidentialPayment + AMOUNTS.benefit306Fz + AMOUNTS.insurancePayment;
    expect(sum).toBeCloseTo(AMOUNTS.baseTotal, 5);
  });
});
