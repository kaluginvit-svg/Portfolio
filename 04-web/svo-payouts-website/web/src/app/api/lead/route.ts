import { NextResponse } from "next/server";
import { buildStoredLeadRecord } from "@/lib/leads/build-stored-lead";
import { getLeadsStorage } from "@/lib/leads/storage/factory";
import { normalizeRuPhone } from "@/lib/phone/normalize-ru-phone";
import { sendLeadTelegramNotification } from "@/lib/telegram/send-lead-notification";
import { sendLeadWebhook } from "@/lib/webhook/send-lead-webhook";
import { leadApiSchema } from "@/lib/validation/lead";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { ok: false, success: false, saved: false, message: "Некорректный запрос" },
      { status: 400 },
    );
  }

  const parsed = leadApiSchema.safeParse(body);
  if (!parsed.success) {
    const flat = parsed.error.flatten();
    return NextResponse.json(
      {
        ok: false,
        success: false,
        saved: false,
        message: "Проверьте поля формы",
        fieldErrors: flat.fieldErrors,
        formErrors: flat.formErrors,
      },
      { status: 400 },
    );
  }

  const phoneFields = normalizeRuPhone(parsed.data.phone);
  const lead = buildStoredLeadRecord(parsed.data, {
    raw: phoneFields.raw,
    normalized: phoneFields.normalized,
  });

  try {
    const storage = getLeadsStorage();
    await storage.save(lead);
  } catch (e) {
    console.error("[leads storage]", e);
    return NextResponse.json(
      {
        ok: false,
        success: false,
        saved: false,
        message:
          "Не удалось сохранить заявку. Попробуйте позже или свяжитесь другим способом.",
      },
      { status: 500 },
    );
  }

  const [tg, wh] = await Promise.all([
    sendLeadTelegramNotification(lead),
    sendLeadWebhook(lead),
  ]);
  const telegramSent = tg.ok === true;
  const webhookSent = wh.ok === true;

  if (telegramSent) {
    try {
      const storage = getLeadsStorage();
      await storage.patchLead(lead.id, { telegramSent: true });
    } catch (e) {
      console.error("[leads storage] patch telegramSent", e);
    }
  }

  return NextResponse.json({
    ok: true,
    success: true,
    saved: true,
    telegramSent,
    webhookSent,
    id: lead.id,
  });
}
