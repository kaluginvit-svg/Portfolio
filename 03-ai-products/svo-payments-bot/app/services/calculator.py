"""Расчёт предварительных сумм (не юридическая консультация)."""

from __future__ import annotations

PRESIDENTIAL_PAYMENT = 5_000_000.0
BENEFIT_306_FZ = 5_524_892.57
INSURANCE_PAYMENT = 3_683_261.71
CHILD_MONTHLY_PAYMENT = 3_311.15


def get_base_total() -> float:
    return PRESIDENTIAL_PAYMENT + BENEFIT_306_FZ + INSURANCE_PAYMENT


def get_personal_share(recipients_count: int) -> float:
    n = max(1, int(recipients_count))
    return get_base_total() / n


def has_child_monthly_payment(applicant_role: str | None) -> bool:
    return applicant_role in ("child_u18", "child_student")


def calculate_lost_income(amount: float, months_waiting: int, monthly_rate: float = 0.012) -> float:
    m = max(0, int(months_waiting))
    return float(amount) * float(monthly_rate) * m


def months_from_waiting_key(key: str | None) -> int | None:
    mp = {"w1": 1, "w2": 2, "w4": 4, "w6": 6}
    return mp.get(key or "")
