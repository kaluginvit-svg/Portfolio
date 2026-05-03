export function formatMoney(n: number | null | undefined, currency?: string | null): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const abs = Math.abs(n);
  const formatted = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(abs);
  const sign = n < 0 ? "−" : "";
  const ccy = currency ? ` ${currency}` : "";
  return `${sign}${formatted}${ccy}`;
}

export function formatPercent(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(2)}%`;
}

/** Value already as ratio (e.g. 0.34 => 34%). */
export function formatDecimalAsPercent(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(2)}%`;
}

/** Already in percent points (e.g. 5.2 means 5.2%). */
export function formatPercentPoints(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${n.toFixed(2)}%`;
}

export function formatRatio(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(2)}%`;
}
