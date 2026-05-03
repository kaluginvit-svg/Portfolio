import { formatTelegramLeadMessageHtml } from "@/lib/telegram/format-lead-message";
import type { StoredLeadRecord } from "@/types/stored-lead";

const TG_API = "https://api.telegram.org";
const TIMEOUT_MS = 12_000;

export type TelegramSendResult =
  | { ok: true }
  | { ok: false; skipped: true; reason: "no_config" }
  | { ok: false; skipped?: false; error: string };

/**
 * Отправляет уведомление о лиде в Telegram Bot API.
 * Не бросает исключений: ошибки и таймауты возвращаются в результате и логируются.
 */
export async function sendLeadTelegramNotification(
  lead: StoredLeadRecord,
): Promise<TelegramSendResult> {
  const token = process.env.TELEGRAM_BOT_TOKEN?.trim();
  const chatId = process.env.TELEGRAM_CHAT_ID?.trim();

  if (!token || !chatId) {
    if (process.env.NODE_ENV === "development") {
      console.warn(
        "[telegram] Уведомление пропущено: задайте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env",
      );
    }
    return { ok: false, skipped: true, reason: "no_config" };
  }

  const text = formatTelegramLeadMessageHtml(lead);
  const url = `${TG_API}/bot${token}/sendMessage`;

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        parse_mode: "HTML",
        disable_web_page_preview: true,
      }),
      signal: controller.signal,
    });

    clearTimeout(timer);

    const data = (await res.json().catch(() => ({}))) as {
      ok?: boolean;
      description?: string;
    };

    if (!res.ok || !data.ok) {
      const msg = data.description ?? `HTTP ${res.status}`;
      console.error("[telegram] sendMessage отклонён:", msg);
      return { ok: false, error: msg };
    }

    return { ok: true };
  } catch (e) {
    const err = e instanceof Error ? e.message : String(e);
    console.error("[telegram] Ошибка отправки:", err);
    return { ok: false, error: err };
  }
}
