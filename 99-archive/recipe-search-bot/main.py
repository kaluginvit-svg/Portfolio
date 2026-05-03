import asyncio
import logging
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

from app.config import BOT_TOKEN, THEMEALDB_API
from app.keyboards import favorite_list_keyboard, main_menu, rating_keyboard, recipe_card_keyboard
from app.services import extract_ingredients, fetch_json, render_meal_text
from app.state import FAVORITES, SEARCH_MODE

logger = logging.getLogger(__name__)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    logger.info("Command /start from user=%s (@%s)", message.from_user.id, message.from_user.username)
    SEARCH_MODE[message.from_user.id] = False
    await message.answer(
        "Привет! Я помогу найти рецепты (TheMealDB) и сохранить их в избранное.",
        reply_markup=main_menu(),
    )


@dp.message(Command("ping"))
async def cmd_ping(message: types.Message) -> None:
    logger.info("Command /ping from user=%s", message.from_user.id)
    await message.answer("pong 🏓")


@dp.message(Command("clear_fav"))
async def cmd_clear_fav(message: types.Message) -> None:
    logger.info("Command /clear_fav from user=%s", message.from_user.id)
    if message.from_user.id in FAVORITES:
        FAVORITES.pop(message.from_user.id, None)
        await message.answer("Избранные рецепты очищены.")
    else:
        await message.answer("Избранных рецептов нет.")


@dp.message(F.text == "🔎 Поиск рецептов")
async def handle_search_entry(message: types.Message) -> None:
    logger.info("Search menu selected user=%s", message.from_user.id)
    SEARCH_MODE[message.from_user.id] = True
    await message.answer(
        "Отправь название блюда для поиска. Например: `pasta`, `chicken`, `Arrabiata`.",
        reply_markup=main_menu(),
    )


@dp.message(F.text == "⭐ Мои рецепты")
async def handle_my_recipes(message: types.Message) -> None:
    logger.info("My recipes selected user=%s", message.from_user.id)
    SEARCH_MODE[message.from_user.id] = False
    user_favs = FAVORITES.get(message.from_user.id, {})
    if not user_favs:
        await message.answer(
            "Избранных рецептов пока нет.",
            reply_markup=main_menu(),
        )
        return

    # сортируем по рейтингу (None в конец), затем по названию
    sorted_meals: List[Tuple[str, Dict[str, object]]] = sorted(
        user_favs.items(),
        key=lambda kv: (-(kv[1].get("rating") or 0), kv[1].get("meal", {}).get("strMeal", "")),
    )
    for meal_id, data in sorted_meals[:15]:
        meal = data.get("meal", {})
        title = meal.get("strMeal") or "Без названия"
        rating = data.get("rating") or 0
        text = f"⭐ {rating}/5 — {title}"
        await message.answer(text, reply_markup=favorite_list_keyboard(meal_id))
    await message.answer("Конец списка.", reply_markup=main_menu())


@dp.callback_query(F.data.startswith("fav:add:"))
async def handle_add_favorite(callback: types.CallbackQuery) -> None:
    meal_id = callback.data.removeprefix("fav:add:")
    logger.info("Add favorite user=%s meal_id=%s", callback.from_user.id, meal_id)
    data = await fetch_json(f"{THEMEALDB_API}/lookup.php?i={meal_id}")
    meals = data.get("meals") if isinstance(data, dict) else None
    if not meals:
        await callback.answer("Не удалось сохранить: рецепт не найден.", show_alert=True)
        return
    meal = meals[0]
    user_favs = FAVORITES.setdefault(callback.from_user.id, {})
    # сохраняем meal и старый рейтинг (если был)
    prev_rating = (user_favs.get(meal_id) or {}).get("rating")
    user_favs[meal_id] = {"meal": meal, "rating": prev_rating}
    await callback.answer("Добавил в избранное.")
    await callback.message.answer(
        "Оцени рецепт от 1 до 5 ⭐:",
        reply_markup=rating_keyboard(meal_id),
    )


@dp.callback_query(F.data.startswith("fav:del:"))
async def handle_delete_favorite(callback: types.CallbackQuery) -> None:
    meal_id = callback.data.removeprefix("fav:del:")
    logger.info("Delete favorite user=%s meal_id=%s", callback.from_user.id, meal_id)
    user_favs = FAVORITES.get(callback.from_user.id, {})
    if meal_id in user_favs:
        user_favs.pop(meal_id, None)
        await callback.answer("Удалил из избранного.")
    else:
        await callback.answer("Этого рецепта нет в избранном.", show_alert=True)


@dp.callback_query(F.data.startswith("open:"))
async def handle_open_recipe(callback: types.CallbackQuery) -> None:
    meal_id = callback.data.removeprefix("open:")
    logger.info("Open recipe user=%s meal_id=%s", callback.from_user.id, meal_id)
    data = await fetch_json(f"{THEMEALDB_API}/lookup.php?i={meal_id}")
    meals = data.get("meals") if isinstance(data, dict) else None
    if not meals:
        await callback.answer("Не удалось загрузить рецепт.", show_alert=True)
        return

    meal = meals[0]
    name = meal.get("strMeal") or "Без названия"
    area = meal.get("strArea") or ""
    category = meal.get("strCategory") or ""
    instructions = meal.get("strInstructions") or "Инструкции недоступны."

    ingredients = extract_ingredients(meal)
    meta = ", ".join(filter(None, [category, area]))
    lines = [f"🍲 {name}"]
    if meta:
        lines.append(meta)
    if ingredients:
        lines.append("\nИнгредиенты:")
        lines.extend(f"• {item}" for item in ingredients)
    lines.append("\nИнструкции:")
    lines.append(instructions)
    youtube = meal.get("strYoutube")
    if youtube:
        lines.append("\nВидеорецепт:")
        lines.append(youtube)
    text = "\n".join(lines)

    thumb = meal.get("strMealThumb")
    if thumb:
        await callback.message.answer_photo(
            thumb,
            caption=f"<b>{name}</b>\n{meta}" if meta else f"<b>{name}</b>",
            parse_mode="HTML",
        )
    await callback.message.answer(
        text[:4000],
        reply_markup=rating_keyboard(meal_id),
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("rate:"))
async def handle_rate_recipe(callback: types.CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    _, meal_id, rating_str = parts
    try:
        rating = int(rating_str)
    except ValueError:
        await callback.answer()
        return
    rating = max(1, min(5, rating))
    logger.info("Rate recipe user=%s meal_id=%s rating=%s", callback.from_user.id, meal_id, rating)

    user_favs = FAVORITES.setdefault(callback.from_user.id, {})
    if meal_id not in user_favs:
        data = await fetch_json(f"{THEMEALDB_API}/lookup.php?i={meal_id}")
        meals = data.get("meals") if isinstance(data, dict) else None
        meal = meals[0] if meals else {}
        user_favs[meal_id] = {"meal": meal, "rating": rating}
    else:
        user_favs[meal_id]["rating"] = rating

    await callback.answer(f"Рейтинг сохранён: {rating} ⭐")


@dp.message(F.text.lower().contains("привет"))
async def greet_on_hello(message: types.Message) -> None:
    logger.info("Greet keyword detected from user=%s text=%r", message.from_user.id, message.text)
    SEARCH_MODE[message.from_user.id] = False
    await message.answer("И тебе привет! 👋", reply_markup=main_menu())


@dp.message(F.text)
async def handle_search_query(message: types.Message) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    logger.info("User input user=%s text=%r", user_id, text)
    if not SEARCH_MODE.get(user_id):
        return
    if len(text) < 2:
        await message.answer("Введи больше символов для поиска.", reply_markup=main_menu())
        return

    logger.info("Search query user=%s q=%r", user_id, text)
    url = f"{THEMEALDB_API}/search.php?s={text}"
    data = await fetch_json(url)
    meals: Optional[List[dict]] = data.get("meals") if isinstance(data, dict) else None
    if not meals:
        await message.answer("Ничего не нашёл. Попробуй другой запрос.", reply_markup=main_menu())
        return

    total = len(meals)
    if total < 3:
        await message.answer("Нашёл меньше трёх вариантов, показываю что есть.", reply_markup=main_menu())

    for meal in meals[: max(3, min(total, 5))]:
        meal_id = meal.get("idMeal") or "unknown"
        caption = render_meal_text(meal)
        thumb = meal.get("strMealThumb")
        if thumb:
            await message.answer_photo(
                thumb,
                caption=caption,
                reply_markup=recipe_card_keyboard(meal_id),
                parse_mode="HTML",
            )
        else:
            await message.answer(caption, reply_markup=recipe_card_keyboard(meal_id), parse_mode="HTML")


@dp.message()
async def handle_fallback(message: types.Message) -> None:
    logger.info("Fallback handler for user=%s text=%r", message.from_user.id, message.text)
    await message.answer("Выбери действие на клавиатуре ниже.", reply_markup=main_menu())


async def main() -> None:
    logger.info("Starting bot polling...")
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

