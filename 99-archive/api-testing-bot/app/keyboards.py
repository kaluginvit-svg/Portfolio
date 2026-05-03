from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_ai_selection_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора AI агента"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔵 OpenRouter")
    kb.button(text="🟡 Chutes")
    kb.button(text="🟢 GigaChat")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def get_remove_keyboard() -> ReplyKeyboardRemove:
    """Удалить клавиатуру"""
    return ReplyKeyboardRemove()
