"""Форматирование сообщений для администратора."""

from __future__ import annotations

import html
from typing import Any

from app.services import calculator as calc
from app.utils.money import format_money_ru


LABEL_DECEASED = {
    "contract": "Военнослужащий по контракту",
    "mobilized": "Мобилизованный",
    "volunteer": "Доброволец",
    "rosgvard": "Росгвардия / иное ведомство",
    "unknown": "Не знаю",
}

LABEL_ROLE = {
    "spouse": "Супруг / супруга",
    "mother": "Мать",
    "father": "Отец",
    "child_u18": "Ребёнок до 18",
    "child_student": "Ребёнок 18–23 очно",
    "representative": "Представитель семьи",
    "complex": "Сложный статус",
}

LABEL_COMPLEX = {
    "unregistered_cohabitation": "Жили вместе, брак не зарегистрирован",
    "kinship_dispute": "Спор о родстве",
    "need_status_help": "Нужна помощь определить статус",
}

LABEL_PROBLEM = {
    "no_response": "Нет ответа",
    "incomplete": "Неполный пакет",
    "rejected": "Отказ",
    "partial": "Часть выплат есть",
    "stuck": "Не понимаем, где зависло",
}

LABEL_SUBMITTED = {
    "military_unit": "Воинская часть",
    "voenkomat": "Военкомат",
    "sogaz": "СОГАЗ",
    "sfr_mfc": "СФР / МФЦ",
    "multiple": "Несколько мест",
}


def _lbl(m: dict[str, str], k: str | None) -> str:
    if not k:
        return "—"
    return m.get(k, k)


def format_admin_lead_message(data: dict[str, Any]) -> str:
    scenario = data.get("scenario")
    sc_ru = "Подаю впервые" if scenario == "first_time" else "Уже подали" if scenario == "already_filed" else "—"

    lines: list[str] = [
        "🆕 <b>Новая заявка</b>",
        "",
        f"👤 Telegram: <code>{data.get('telegram_user_id')}</code>",
        f"Username: @{html.escape(str(data.get('telegram_username')), quote=False)}"
        if data.get("telegram_username")
        else "Username: —",
        "",
        f"📌 Сценарий: <b>{sc_ru}</b>",
        f"Статус погибшего: <b>{_lbl(LABEL_DECEASED, data.get('status_of_deceased'))}</b>",
        f"Кто обращается: <b>{_lbl(LABEL_ROLE, data.get('applicant_role'))}</b>",
    ]
    if data.get("complex_status"):
        lines.append(f"Уточнение: <b>{_lbl(LABEL_COMPLEX, data.get('complex_status'))}</b>")
    lines.append(f"👨‍👩‍👧 Получателей (оценка): <b>{data.get('recipients_count', '—')}</b>")
    lines.append(f"Регион: <b>{html.escape(str(data.get('region') or '—'), quote=False)}</b>")

    if scenario == "already_filed":
        lines.extend(
            [
                "",
                "⏳ <b>Задержка</b>",
                f"Проблема: {_lbl(LABEL_PROBLEM, data.get('problem_type'))}",
                f"Куда подавали: {_lbl(LABEL_SUBMITTED, data.get('submitted_to'))}",
                f"Месяцев (оценка): {data.get('months_waiting', '—')}",
            ]
        )
        if data.get("estimated_lost_income") is not None:
            try:
                lost = float(data["estimated_lost_income"])
                lines.append(f"Оценка «цены ожидания»: <b>{format_money_ru(lost)} ₽</b>")
            except (TypeError, ValueError):
                pass

    if scenario == "first_time" and data.get("selected_documents"):
        docs = data.get("selected_documents")
        if isinstance(docs, list):
            doc_line = ", ".join(str(x) for x in docs)
        else:
            doc_line = str(docs)
        lines.append(f"📄 Документы: {html.escape(doc_line, quote=False)}")

    bt = data.get("base_total")
    ps = data.get("personal_share")
    lines.extend(
        [
            "",
            "💰 <b>Предварительный расчёт</b>",
            f"База семьи: <b>{format_money_ru(float(bt))} ₽</b>" if bt is not None else "",
            f"Доля заявителя: <b>{format_money_ru(float(ps))} ₽</b>" if ps is not None else "",
        ]
    )
    lines = [x for x in lines if x != ""]

    if data.get("child_monthly_payment_applicable"):
        lines.append(f"Ежемес. на ребёнка: ~{format_money_ru(calc.CHILD_MONTHLY_PAYMENT)} ₽")

    lines.extend(
        [
            "",
            "📞 <b>Контакты</b>",
            f"Имя: <b>{html.escape(str(data.get('lead_name') or '—'), quote=False)}</b>",
            f"Телефон: <b>{html.escape(str(data.get('normalized_phone') or data.get('phone') or '—'), quote=False)}</b>",
            f"Доп. контакт: {html.escape(str(data.get('contact_method')), quote=False) if data.get('contact_method') else '—'}",
            f"Комментарий: {html.escape(str(data.get('comment')), quote=False) if data.get('comment') else '—'}",
        ]
    )
    return "\n".join(lines)
