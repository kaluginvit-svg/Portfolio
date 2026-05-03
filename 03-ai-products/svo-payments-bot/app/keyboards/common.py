"""Общие ряды клавиатур."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def row_back() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text="◀️ Назад", callback_data="nav:back")]


def row_home() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text="🏠 В начало", callback_data="nav:home")]


def nav_rows(*, with_home: bool = True) -> list[list[InlineKeyboardButton]]:
    rows = [row_back()]
    if with_home:
        rows.append(row_home())
    return rows


def attach_nav(kb: InlineKeyboardMarkup, *, with_home: bool = True) -> InlineKeyboardMarkup:
    rows = list(kb.inline_keyboard)
    rows.extend(nav_rows(with_home=with_home))
    return InlineKeyboardMarkup(inline_keyboard=rows)
