import type { PlanVsFactResponse } from "@/types/finance";
import { formatMoney, formatPercentPoints } from "@/lib/formatters";

export function buildPlanFactCommentary(v: PlanVsFactResponse): string {
  const { variance_abs, variance_pct } = v;
  const dir = variance_abs >= 0 ? "above" : "below";
  const pct =
    variance_pct !== null && variance_pct !== undefined ? ` (${formatPercentPoints(variance_pct)} vs plan)` : "";
  return `Total fact is ${formatMoney(Math.abs(variance_abs))} ${dir} plan on a net basis${pct}. Review category breakdown for drivers — typically revenue shortfalls or OPEX overruns explain the largest variances.`;
}
