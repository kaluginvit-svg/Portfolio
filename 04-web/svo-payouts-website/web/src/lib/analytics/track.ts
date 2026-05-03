import { ANALYTICS_EVENTS, type AnalyticsEventName } from "@/lib/analytics/events";

const GA_ID = process.env.NEXT_PUBLIC_GA_ID?.trim() || "";

function ymIdFromWindow(): string {
  if (typeof window === "undefined") return "";
  const id = (window as Window & { __SVO_YM_ID?: string }).__SVO_YM_ID;
  return typeof id === "string" ? id.trim() : "";
}

function ymCounterId(): number | null {
  const raw =
    ymIdFromWindow() || process.env.NEXT_PUBLIC_YM_ID?.trim().replace(/\r/g, "") || "";
  if (!raw) return null;
  const n = Number(raw.replace(/\D/g, ""));
  return Number.isFinite(n) && n > 0 ? n : null;
}

function sendGtag(
  eventName: string,
  params?: Record<string, string | number | boolean | undefined>,
) {
  if (typeof window === "undefined" || !GA_ID) return;
  const g = window.gtag;
  if (typeof g !== "function") return;
  const payload = Object.fromEntries(
    Object.entries(params ?? {}).filter(([, v]) => v !== undefined),
  ) as Record<string, string | number | boolean>;
  g("event", eventName, payload);
}

function sendYmReachGoal(
  eventName: string,
  params?: Record<string, string | number | boolean | undefined>,
) {
  const id = ymCounterId();
  if (typeof window === "undefined" || id == null) return;
  const ym = window.ym;
  if (typeof ym !== "function") return;
  const filtered: Record<string, string | number> = {};
  for (const [k, v] of Object.entries(params ?? {})) {
    if (v === undefined) continue;
    filtered[k] = typeof v === "boolean" ? (v ? 1 : 0) : v;
  }
  if (Object.keys(filtered).length > 0) {
    ym(id, "reachGoal", eventName, filtered);
  } else {
    ym(id, "reachGoal", eventName);
  }
}

/**
 * Отправка кастомного события в GA4 и Яндекс.Метрику (если заданы env).
 * Безопасно вызывать только на клиенте (после загрузки скриптов).
 */
export function trackEvent(
  name: AnalyticsEventName,
  params?: Record<string, string | number | boolean | undefined>,
): void {
  if (typeof window === "undefined") return;
  const eventId = ANALYTICS_EVENTS[name];
  sendGtag(eventId, params);
  sendYmReachGoal(eventId, params);
}
