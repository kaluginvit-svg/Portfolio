"""Форматирование сумм для отображения в RU-локали."""

from __future__ import annotations


def format_money_ru(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")
