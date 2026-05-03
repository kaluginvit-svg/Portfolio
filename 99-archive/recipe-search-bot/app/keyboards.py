from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔎 Поиск рецептов")
    builder.button(text="⭐ Мои рецепты")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def recipe_card_keyboard(meal_id: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❤️ Добавить в избранное", callback_data=f"fav:add:{meal_id}")
    builder.button(text="📄 Показать рецепт", callback_data=f"open:{meal_id}")
    builder.adjust(2)
    return builder.as_markup()


def rating_keyboard(meal_id: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=f"⭐ {i}", callback_data=f"rate:{meal_id}:{i}")
    builder.adjust(5)
    return builder.as_markup()


def favorite_list_keyboard(meal_id: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"fav:del:{meal_id}")
    builder.button(text="🔍 Открыть рецепт", callback_data=f"open:{meal_id}")
    builder.adjust(2)
    return builder.as_markup()

