"""Формулы выплат — используйте через этот модуль или app.services.calculator."""

from app.services.calculator import (
    CHILD_MONTHLY_PAYMENT,
    calculate_lost_income,
    get_base_total,
    get_personal_share,
    has_child_monthly_payment,
)

__all__ = [
    "CHILD_MONTHLY_PAYMENT",
    "calculate_lost_income",
    "get_base_total",
    "get_personal_share",
    "has_child_monthly_payment",
]
