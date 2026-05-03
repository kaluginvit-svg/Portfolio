import { describe, expect, it } from "vitest";
import { normalizeRuPhone } from "@/lib/phone/normalize-ru-phone";

describe("normalizeRuPhone", () => {
  it("10 цифр без кода страны → +7", () => {
    const r = normalizeRuPhone("9001234567");
    expect(r.digits).toBe("79001234567");
    expect(r.normalized).toBe("+79001234567");
  });

  it("8XXXXXXXXXXX", () => {
    const r = normalizeRuPhone("89001234567");
    expect(r.normalized).toBe("+79001234567");
  });

  it("+7 и пробелы", () => {
    const r = normalizeRuPhone("+7 (900) 123-45-67");
    expect(r.normalized).toBe("+79001234567");
    expect(r.digits).toBe("79001234567");
  });

  it("короткий номер — без выдуманного +7", () => {
    const r = normalizeRuPhone("12345");
    expect(r.digits).toBe("12345");
    expect(r.normalized).toBe("12345");
  });
});
