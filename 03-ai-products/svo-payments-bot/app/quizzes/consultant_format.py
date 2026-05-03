"""Тексты уведомлений консультанту по квизам."""

from __future__ import annotations

from typing import Any


def format_clarify_consultant_message(derived: dict[str, Any]) -> str:
    return (
        "Новая заявка из квиза\n\n"
        f"Этап: {derived['stage_label']} — {derived['stage_score']}/100\n"
        f"Фаза: {derived.get('journey_phase_label', derived['journey_phase'])}\n"
        f"Приоритет: {derived['lead_temperature_label']}\n\n"
        "Что уже есть:\n"
        f"— Свидетельство о смерти: {derived['death_certificate_status']}\n"
        f"— Документ из части: {derived['military_notice_status']}\n"
        f"— Документы о родстве: {derived['kinship_docs_status']}\n"
        f"— Пакет для подачи: {derived['submission_pack_status']}\n\n"
        "Статус подачи:\n"
        f"— {derived['filing_status']}\n"
        f"— Куда подавали: {derived['filing_route_label']}\n\n"
        "Что происходит сейчас:\n"
        f"— {derived['current_case_state']}\n\n"
        "Главный стопор:\n"
        f"— {derived['primary_blocker_label']}\n"
        f"{derived['secondary_blocker_line']}\n\n"
        "Что хочет понять:\n"
        f"— {derived['user_focus']}\n\n"
        "Кратко для консультанта:\n"
        f"{derived['consultant_summary']}\n\n"
        "Что сделать консультанту:\n"
        f"1. {derived['consultant_step_1']}\n"
        f"2. {derived['consultant_step_2']}\n"
        f"3. {derived['consultant_step_3']}"
    )


def format_calculate_consultant_message(
    *,
    lead_name: str,
    lead_phone: str,
    calc: dict[str, Any],
) -> str:
    clar = calc.get("clarification_note") or ""
    reg = calc.get("regional_note") or ""
    lines = [
        "Новая заявка из квиза\n",
        "Тип квиза: Расчёт выплат",
        f"Имя: {lead_name}",
        f"Телефон: {lead_phone}\n",
        f"Итоговый ориентировочный федеральный расчёт: {calc['headline_amount']}",
        f"Разовые выплаты семье: {calc['lump_sum_total']}",
        f"Ориентировочная доля заявителя: {calc['personal_share_text']}",
        f"Ежемесячно на детей: {calc['monthly_children_text']}",
        f"Статус расчёта: {calc['precision_label']}\n",
        "Разбивка:",
        f"— Президентская выплата: {calc['consultant_breakdown_president_payment']}",
        f"— Единовременное пособие: {calc['consultant_breakdown_306_payment']}",
        f"— Страховая сумма: {calc['consultant_breakdown_insurance_52']}",
        f"— Ежемесячное пособие детям: {calc['consultant_breakdown_monthly_child_allowance']}",
        f"— Ежемесячная пенсия детям: {calc['consultant_breakdown_monthly_child_pension']}\n",
        "Примечание:",
    ]
    if clar:
        lines.append(clar)
    if reg:
        lines.append(reg)
    if not clar and not reg:
        lines.append("—")
    return "\n".join(lines)
