"""Расчёт выплат для квиза «Рассчитать выплаты»."""

from __future__ import annotations

from typing import Any

PRESIDENT_PAYMENT = 5_000_000.0
LUMP_SUM_306 = 5_524_892.57
INSURANCE_52 = 3_683_261.71

BASE_LUMP_SUM_STANDARD = 14_208_154.28
BASE_LUMP_SUM_CONSERVATIVE = 10_524_892.57

CHILD_MONTHLY_ALLOWANCE_PER_CHILD = 3311.15


def _recipients_int(raw: str | None) -> int | None:
    if not raw or raw == "unknown":
        return None
    if raw == "5_plus":
        return 5
    try:
        return int(raw)
    except ValueError:
        return None


def _children_int(raw: str | None) -> int:
    if not raw or raw == "0":
        return 0
    if raw == "3_plus":
        return 3
    try:
        return int(raw)
    except ValueError:
        return 0


def _child_pension_per_child(death_basis: str | None) -> tuple[float, bool]:
    if death_basis == "duty":
        return 15379.66, False
    if death_basis == "disease":
        return 11534.75, False
    return 15379.66, True


def compute_payment_result(answers: dict[str, str]) -> dict[str, Any]:
    service = answers.get("service_status") or ""
    applicant = answers.get("applicant_role") or ""
    rec_raw = answers.get("recipients_count")
    children_raw = answers.get("children_count")
    death_basis = answers.get("death_basis") or ""
    ambiguity = answers.get("ambiguity_flag") or ""
    calc_mode = answers.get("calc_mode") or ""

    children_n = _children_int(children_raw)
    rec_n = _recipients_int(rec_raw)

    force_line = service in ("contract_mobilized", "force_department")
    volunteer_line = service in ("volunteer", "unknown")

    disputed = (
        ambiguity in ("yes", "unknown")
        or applicant == "cohabitation_no_marriage"
        or rec_raw == "unknown"
    )

    pension_rate, death_unknown_flag = _child_pension_per_child(death_basis)

    if disputed:
        if force_line:
            base_lump = BASE_LUMP_SUM_STANDARD
            insurance_52 = INSURANCE_52
            headline_amount = "до 14 208 154,28 ₽"
        else:
            base_lump = BASE_LUMP_SUM_CONSERVATIVE
            insurance_52 = 0.0
            headline_amount = "от 10 524 892,57 ₽"
        branch = "disputed"
    elif volunteer_line:
        base_lump = BASE_LUMP_SUM_CONSERVATIVE
        insurance_52 = 0.0
        headline_amount = "от 10 524 892,57 ₽"
        branch = "conservative"
    else:
        base_lump = BASE_LUMP_SUM_STANDARD
        insurance_52 = INSURANCE_52
        headline_amount = "14 208 154,28 ₽"
        branch = "standard"

    if rec_n is None:
        personal_share = None
    else:
        personal_share = round(base_lump / rec_n, 2)

    monthly_allowance = round(CHILD_MONTHLY_ALLOWANCE_PER_CHILD * children_n, 2)
    monthly_pension = round(pension_rate * children_n, 2)
    monthly_children_total = round(monthly_allowance + monthly_pension, 2)

    preliminary_ok = branch == "standard" and not death_unknown_flag
    precision_key = "preliminary_ok" if preliminary_ok else "needs_clarification"
    precision_label = "Предварительный расчёт" if precision_key == "preliminary_ok" else "Требует уточнений"

    clarification_note = ""
    if precision_key == "needs_clarification":
        clarification_note = (
            "Сумма рассчитана по наиболее вероятному федеральному сценарию и требует уточнений."
        )

    regional_note = ""
    if calc_mode == "federal_plus_region":
        regional_note = "Региональные выплаты не включены в автоматический расчёт и требуют отдельной проверки."

    radiation_module_status = "not_included"
    radiation_module_note = (
        "Дополнительный модуль по радиационным/техногенным основаниям не включён в автоматический расчёт."
    )

    headline_prefix = "Ваш ориентировочный федеральный расчёт"

    def _share_text() -> str:
        if personal_share is None:
            return "требует уточнений"
        return f"{personal_share:,.2f}".replace(",", " ").replace(".", ",") + " ₽"

    def _monthly_text() -> str:
        if children_n == 0:
            return "0 ₽/мес"
        return f"{monthly_children_total:,.2f}".replace(",", " ").replace(".", ",") + " ₽/мес"

    lump_formatted = f"{base_lump:,.2f}".replace(",", " ").replace(".", ",") + " ₽"

    consultant_summary = (
        f"Итоговый ориентировочный федеральный расчёт: {headline_amount}. "
        f"Разовые выплаты семье: {lump_formatted}. "
        f"Ориентировочная доля заявителя: {_share_text()}. "
        f"Ежемесячно на детей: {_monthly_text()}. "
        f"Статус расчёта: {precision_label}."
    )
    if clarification_note:
        consultant_summary += " " + clarification_note

    region_included = False
    region_note = (
        "Региональные выплаты не включены в автоматический расчёт и требуют отдельной проверки."
    )

    return {
        "headline_prefix": headline_prefix,
        "headline_amount": headline_amount,
        "lump_sum_total": base_lump,
        "personal_share": personal_share,
        "monthly_children_total": monthly_children_total,
        "monthly_allowance_part": monthly_allowance,
        "monthly_pension_part": monthly_pension,
        "precision_key": precision_key,
        "precision_label": precision_label,
        "clarification_note": clarification_note,
        "regional_note": regional_note,
        "radiation_module_status": radiation_module_status,
        "radiation_module_note": radiation_module_note,
        "consultant_summary": consultant_summary.strip(),
        "consultant_breakdown_president_payment": PRESIDENT_PAYMENT,
        "consultant_breakdown_306_payment": LUMP_SUM_306,
        "consultant_breakdown_insurance_52": insurance_52,
        "consultant_breakdown_monthly_child_allowance": monthly_allowance,
        "consultant_breakdown_monthly_child_pension": monthly_pension,
        "consultant_breakdown_region_included": region_included,
        "consultant_breakdown_region_note": region_note,
        "branch": branch,
        "children_count_int": children_n,
        "needs_clarification_death_basis": death_unknown_flag,
        "personal_share_text": _share_text(),
        "monthly_children_text": _monthly_text(),
    }
