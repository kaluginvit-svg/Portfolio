/** Убирает пробелы, дефисы, скобки и нецифровые символы для подсчёта/нормализации. */
function digitsOnly(input: string): string {
  return input.replace(/\D/g, "");
}

/**
 * Нормализация российского номера для хранения и звонков.
 * - сохраняет исходную строку (после trim) как raw
 * - 8XXXXXXXXXX → +7XXXXXXXXXX
 * - 7XXXXXXXXXX → +7XXXXXXXXXX
 * - 10 цифр (код без страны) → +7...
 */
export function normalizeRuPhone(input: string): {
  raw: string;
  normalized: string;
  digits: string;
} {
  const raw = input.trim();
  let d = digitsOnly(raw);
  if (d.length === 11 && d.startsWith("8")) {
    d = `7${d.slice(1)}`;
  }
  if (d.length === 10) {
    d = `7${d}`;
  }
  if (d.length === 11 && d.startsWith("7")) {
    return {
      raw,
      normalized: `+${d}`,
      digits: d,
    };
  }
  /* иностранный или нестандартный — отдаём плюс и цифры как есть */
  if (d.length >= 10 && raw.startsWith("+")) {
    return { raw, normalized: `+${d}`, digits: d };
  }
  if (d.length >= 10) {
    return { raw, normalized: `+${d}`, digits: d };
  }
  return { raw, normalized: raw, digits: d };
}
