import { formatRub } from "@/lib/calculator";
import { escapeHtml } from "@/lib/telegram/escape-html";
import type { StoredLeadRecord } from "@/types/stored-lead";

function scenarioLine(scenario: StoredLeadRecord["scenario"]): string {
  if (scenario === "A") return "Подаю впервые";
  if (scenario === "B") return "Уже подали, но вопрос не решается";
  return "—";
}

function flowLine(lead: StoredLeadRecord): string {
  if (lead.flowMode === "fresh") return "Узнать выплаты (fresh)";
  if (lead.flowMode === "clarify") return "Прояснить ситуацию (документы)";
  return scenarioLine(lead.scenario);
}

function orDash(v: string | null | undefined): string {
  if (v === null || v === undefined || v === "") return "—";
  return v;
}

function formatDateRu(iso: string): string {
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatTelegramLeadMessageHtml(lead: StoredLeadRecord): string {
  const lines: string[] = [];

  lines.push("🆕 <b>Новый лид с сайта</b>");
  lines.push("");
  lines.push(`<b>Режим:</b> ${escapeHtml(flowLine(lead))}`);

  if (lead.flowMode === "clarify") {
    lines.push(`<b>Регион (форма):</b> ${escapeHtml(lead.region)}`);
    lines.push("");
    lines.push("📋 <b>Ответы про документы</b>");
    lines.push(escapeHtml(orDash(lead.documentsOnHand)));
    lines.push("");
    if (lead.clarifyInsight?.telegram_summary_plain) {
      lines.push("🧭 <b>Квиз: сводка для консультанта</b>");
      lines.push(
        escapeHtml(lead.clarifyInsight.telegram_summary_plain).replaceAll(
          "\n",
          "<br/>",
        ),
      );
      lines.push("");
    }
    lines.push(
      "<i>Предварительный расчёт суммы на сайте не выполнялся — только опрос про документы.</i>",
    );
  } else {
    lines.push(`<b>Кто обращается:</b> ${escapeHtml(orDash(lead.applicantRole))}`);
    lines.push(
      `<b>Статус погибшего:</b> ${escapeHtml(orDash(lead.statusOfDeceased))}`,
    );
    if (lead.complexStatus) {
      lines.push(`<b>Уточнение по статусу:</b> ${escapeHtml(lead.complexStatus)}`);
    }
    lines.push(`<b>Число получателей:</b> ${lead.recipientsCount ?? "—"}`);
    lines.push(`<b>Регион:</b> ${escapeHtml(lead.region)}`);

    if (lead.documentsOnHand) {
      lines.push(`<b>Документы на руках:</b> ${escapeHtml(lead.documentsOnHand)}`);
    }
    if (lead.freshConsultantPayload?.consultant_summary) {
      lines.push("");
      lines.push("📊 <b>Предрасчёт (консультант)</b>");
      lines.push(escapeHtml(lead.freshConsultantPayload.consultant_summary));
    }

    if (lead.scenario === "B") {
      lines.push("");
      lines.push("⏳ <b>Устаревшие поля сценария B</b>");
      lines.push(`<b>Проблема (кратко):</b> ${escapeHtml(orDash(lead.problemType))}`);
      lines.push(`<b>Куда обращались:</b> ${escapeHtml(orDash(lead.submittedTo))}`);
    }

    lines.push("");
    lines.push("📊 <b>Предварительный расчёт</b>");
    lines.push(`<b>Общая сумма (ориентир):</b> ${escapeHtml(formatRub(lead.baseTotal))}`);
    lines.push(
      `<b>Ориентировочная доля:</b> ${escapeHtml(formatRub(lead.personalShare))}`,
    );
  }

  lines.push("");
  lines.push("📞 <b>Контакты</b>");
  lines.push(`<b>Имя:</b> ${escapeHtml(lead.name)}`);
  lines.push(`<b>Телефон:</b> ${escapeHtml(lead.phone)}`);
  if (lead.phoneRaw && lead.phoneRaw !== lead.phone) {
    lines.push(`<b>Как ввели в форме:</b> ${escapeHtml(lead.phoneRaw)}`);
  }
  lines.push(`<b>Мессенджер:</b> ${escapeHtml(orDash(lead.messenger))}`);
  lines.push(`<b>Email:</b> ${escapeHtml(orDash(lead.email))}`);

  lines.push("");
  lines.push("💬 <b>Комментарий</b>");
  lines.push(escapeHtml(orDash(lead.comment)));

  lines.push("");
  lines.push("📎 <b>UTM</b>");
  lines.push(`source: ${escapeHtml(orDash(lead.utm_source))}`);
  lines.push(`medium: ${escapeHtml(orDash(lead.utm_medium))}`);
  lines.push(`campaign: ${escapeHtml(orDash(lead.utm_campaign))}`);

  lines.push("");
  lines.push(`🕐 <b>Дата:</b> ${escapeHtml(formatDateRu(lead.createdAt))}`);

  const contact = process.env.CONTACT_TEXT?.trim();
  if (contact) {
    lines.push("");
    lines.push("ℹ️ <b>Служебная заметка</b> <i>(CONTACT_TEXT)</i>");
    lines.push(escapeHtml(contact));
  }

  let text = lines.join("\n");
  const max = 3900;
  if (text.length > max) {
    text = `${text.slice(0, max)}…`;
  }
  return text;
}
