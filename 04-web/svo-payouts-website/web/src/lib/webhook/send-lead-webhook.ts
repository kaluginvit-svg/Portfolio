import type { StoredLeadRecord } from "@/types/stored-lead";

const TIMEOUT_MS = 12_000;

export type LeadWebhookSendResult =
  | { ok: true }
  | { ok: false; skipped: true; reason: "no_config" }
  | { ok: false; error: string };

/**
 * POST JSON о лиде на вебхук (n8n, Make, свой endpoint).
 * Не бросает исключений. Без LEAD_WEBHOOK_URL — пропуск.
 */
export async function sendLeadWebhook(
  lead: StoredLeadRecord,
): Promise<LeadWebhookSendResult> {
  const url = process.env.LEAD_WEBHOOK_URL?.trim();
  if (!url) {
    console.warn(
      "[webhook] Пропуск: LEAD_WEBHOOK_URL не задан (проверьте .env у docker-compose на VPS, не только web/.env)",
    );
    return { ok: false, skipped: true, reason: "no_config" };
  }

  const secret = process.env.LEAD_WEBHOOK_SECRET?.trim();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (secret) {
    headers.Authorization = `Bearer ${secret}`;
  }

  const body = JSON.stringify({
    event: "lead.created",
    lead,
  });

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const res = await fetch(url, {
      method: "POST",
      headers,
      body,
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      console.error(
        "[webhook] Ответ не OK:",
        res.status,
        text.slice(0, 500),
      );
      return { ok: false, error: `HTTP ${res.status}` };
    }

    console.log("[webhook] OK, lead id=", lead.id);
    return { ok: true };
  } catch (e) {
    const err = e instanceof Error ? e.message : String(e);
    console.error("[webhook] Ошибка запроса:", err);
    return { ok: false, error: err };
  }
}
