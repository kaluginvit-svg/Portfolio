/** Доля «стоимости ожидания» в месяц (как в UI результата). */
export const DELAY_LOSS_FACTOR_PER_MONTH = 0.012;

/**
 * Условные потери из-за ожидания (семья и доля пользователя).
 * Возвращает null, если месяцев нет или они неположительные.
 */
export function computeDelayLossRub(
  federalTotal: number,
  personalShare: number,
  waitMonths: number | null | undefined,
): { delayFamilyRub: number; delayShareRub: number } | null {
  if (waitMonths == null || !Number.isFinite(waitMonths) || waitMonths <= 0) {
    return null;
  }
  if (!Number.isFinite(federalTotal) || !Number.isFinite(personalShare)) {
    return null;
  }
  const f = DELAY_LOSS_FACTOR_PER_MONTH;
  return {
    delayFamilyRub: federalTotal * f * waitMonths,
    delayShareRub: personalShare * f * waitMonths,
  };
}
