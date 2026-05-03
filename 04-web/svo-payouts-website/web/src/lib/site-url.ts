/** Базовый URL сайта для metadataBase и Open Graph. В .env задайте полный адрес (с протоколом или домен). */
export function resolveSiteUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SITE_URL?.trim().replace(/\/$/, "");
  if (!raw) return "http://localhost:3000";
  const candidate =
    raw.startsWith("http://") || raw.startsWith("https://") ? raw : `https://${raw}`;
  try {
    new URL(candidate);
    return candidate;
  } catch {
    return "http://localhost:3000";
  }
}
