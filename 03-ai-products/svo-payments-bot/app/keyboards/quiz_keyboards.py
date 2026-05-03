"""Клавиатуры квизов."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.keyboards.common import attach_nav
from app.quizzes.models import QuizStep


def _cb_answer(step_id: str, value: str) -> str:
    return f"qza|{step_id}|{value}"


def for_quiz_step(step: QuizStep) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for opt in step.options:
        rows.append(
            [InlineKeyboardButton(text=opt.label, callback_data=_cb_answer(step.id, opt.value))]
        )
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    return attach_nav(kb)


def region_nav() -> InlineKeyboardMarkup:
    return attach_nav(InlineKeyboardMarkup(inline_keyboard=[]))


def quiz_consent_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен и продолжить", callback_data="qz:consent:yes")],
            [InlineKeyboardButton(text="❌ Не согласен", callback_data="qz:consent:no")],
        ]
    )
    return attach_nav(kb)


def quiz_consent_refused_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В начало", callback_data="nav:home")],
        ]
    )


def phone_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def quiz_lead_name_nav() -> InlineKeyboardMarkup:
    return attach_nav(InlineKeyboardMarkup(inline_keyboard=[]))


def quiz_lead_phone_nav() -> InlineKeyboardMarkup:
    return attach_nav(InlineKeyboardMarkup(inline_keyboard=[]))
