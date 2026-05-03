import { describe, expect, it } from "vitest";
import {
  computeDelayLossRub,
  DELAY_LOSS_FACTOR_PER_MONTH,
} from "@/lib/calculator/delay-loss";

describe("computeDelayLossRub", () => {
  it("null при отсутствии месяцев или ≤0", () => {
    expect(computeDelayLossRub(1e7, 1e6, null)).toBeNull();
    expect(computeDelayLossRub(1e7, 1e6, undefined)).toBeNull();
    expect(computeDelayLossRub(1e7, 1e6, 0)).toBeNull();
    expect(computeDelayLossRub(1e7, 1e6, -1)).toBeNull();
  });

  it("формула совпадает с UI: 1.2% в месяц от базы", () => {
    const federal = 10_000_000;
    const share = 5_000_000;
    const m = 4;
    const out = computeDelayLossRub(federal, share, m);
    expect(out).not.toBeNull();
    expect(out!.delayFamilyRub).toBeCloseTo(
      federal * DELAY_LOSS_FACTOR_PER_MONTH * m,
      5,
    );
    expect(out!.delayShareRub).toBeCloseTo(
      share * DELAY_LOSS_FACTOR_PER_MONTH * m,
      5,
    );
  });

  it("NaN в суммах → null", () => {
    expect(computeDelayLossRub(NaN, 1, 2)).toBeNull();
    expect(computeDelayLossRub(1, NaN, 2)).toBeNull();
  });
});
