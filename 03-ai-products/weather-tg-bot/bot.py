"""
Каркас Telegram-бота: главное меню и маршрутизация по кнопкам.
"""
import logging
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import telebot  # type: ignore[import-untyped]
from telebot import types  # type: ignore[import-untyped]

from weather_app import (
    get_coordinates,
    get_current_weather,
    get_forecast_5d3h,
    get_air_pollution,
    analyze_air_pollution,
    localize_weather_description,
)
from storage import load_user, save_user

logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

pending_city: dict[int, bool] = {}
pending_compare: dict[int, bool] = {}
pending_extended: dict[int, bool] = {}
user_forecasts: dict[int, dict[str, list]] = {}

# Тексты кнопок главного меню (с эмодзи) — используются в клавиатуре и в маппере
BTN_CURRENT = "☀️ Текущая погода"
BTN_FORECAST = "📅 Прогноз на 5 дней"
BTN_LOCATION = "📍 Отправить местоположение"
BTN_COMPARE = "📊 Сравнить города"
BTN_EXTENDED = "🌐 Расширенные данные"
BTN_NOTIFICATIONS = "🔔 Уведомления"

MENU_ACTIONS = {
    BTN_CURRENT: "current_weather",
    BTN_FORECAST: "forecast",
    BTN_COMPARE: "compare",
    BTN_EXTENDED: "extended",
    BTN_NOTIFICATIONS: "notifications",
}


def _get_menu_action(text: str) -> str | None:
    return MENU_ACTIONS.get((text or "").strip())


def build_main_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton(BTN_CURRENT),
        types.KeyboardButton(BTN_FORECAST),
    )
    markup.row(
        types.KeyboardButton(BTN_LOCATION, request_location=True),
        types.KeyboardButton(BTN_NOTIFICATIONS),
    )
    markup.row(
        types.KeyboardButton(BTN_COMPARE),
        types.KeyboardButton(BTN_EXTENDED),
    )
    return markup


def _has_valid_coords(user: dict | None) -> bool:
    if not user or not isinstance(user, dict):
        return False
    try:
        lat = user.get("lat")
        lon = user.get("lon")
        if lat is None or lon is None:
            return False
        lat, lon = float(lat), float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (TypeError, ValueError):
        return False


def maybe_send_notification(message: types.Message) -> None:
    """При включённых уведомлениях и истечении интервала отправляет краткую погоду. Ошибки не пробрасывает."""
    try:
        if not message or not message.from_user:
            return
        user_id = message.from_user.id
        user = load_user(user_id)
        n = user.get("notifications") or {}
        if not n.get("enabled"):
            return
        if not _has_valid_coords(user):
            return
        lat = float(user.get("lat"))
        lon = float(user.get("lon"))
        interval_h = n.get("interval_h")
        if interval_h is None:
            return
        last_sent = n.get("last_sent")
        now = time.time()
        if last_sent is not None and (now - last_sent) < interval_h * 3600:
            return
        data = get_current_weather(lat, lon)
        if data is None:
            return
        text = _format_current_weather(data)
        bot.send_message(message.chat.id, text)
        n["last_sent"] = now
        n["enabled"] = True
        n["interval_h"] = interval_h
        user["notifications"] = n
        save_user(user_id, user)
    except Exception as e:
        logger.warning("maybe_send_notification failed: %s", e)


def _format_current_weather(data: dict) -> str:
    main = data.get("main") or {}
    temp = main.get("temp")
    feels = main.get("feels_like")
    humidity = main.get("humidity")
    pressure = main.get("pressure")
    weather_list = data.get("weather") or []
    raw_desc = (weather_list[0].get("description") or "—") if weather_list else "—"
    desc = localize_weather_description(raw_desc)
    wind = data.get("wind") or {}
    speed = wind.get("speed")
    name = data.get("name") or ""

    parts = []
    if name:
        parts.append(f"Погода в {name}")
    if temp is not None:
        parts.append(f"Температура: {temp:.0f}°C")
    if feels is not None:
        parts.append(f"Ощущается как: {feels:.0f}°C")
    parts.append(f"Описание: {desc}")
    if humidity is not None:
        parts.append(f"Влажность: {humidity}%")
    if pressure is not None:
        parts.append(f"Давление: {pressure:.0f} гПа")
    if speed is not None:
        parts.append(f"Ветер: {speed:.0f} м/с")
    return "\n".join(parts) if parts else "Нет данных."


def _format_inline_weather_message(data: dict) -> str:
    text = _format_current_weather(data)
    city_id = data.get("id")
    if city_id is not None:
        text += f"\n\nПрогноз: https://openweathermap.org/city/{city_id}"
    return text


def _send_current_weather(message: types.Message, lat: float, lon: float) -> None:
    data = get_current_weather(lat, lon)
    if data is None:
        bot.reply_to(message, "Не удалось получить данные, попробуйте позже.")
        return
    try:
        text = _format_current_weather(data)
        bot.reply_to(message, text)
    except Exception as e:
        logger.warning("Format/send weather failed: %s", e)
        bot.reply_to(message, "Не удалось получить данные, попробуйте позже.")


def _ask_for_location(message: types.Message) -> None:
    bot.reply_to(
        message,
        "Пожалуйста, отправьте location.",
        reply_markup=build_main_keyboard(),
    )


def _build_notif_on_off_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Включить", callback_data="notif:on"),
        types.InlineKeyboardButton("Выключить", callback_data="notif:off"),
    )
    return markup


def _build_notif_interval_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("1 ч", callback_data="notif:int:1"),
        types.InlineKeyboardButton("2 ч", callback_data="notif:int:2"),
        types.InlineKeyboardButton("3 ч", callback_data="notif:int:3"),
        types.InlineKeyboardButton("6 ч", callback_data="notif:int:6"),
    )
    return markup


_COMPONENT_LABELS = {
    "pm2_5": "PM2.5",
    "pm10": "PM10",
    "no2": "NO2",
    "o3": "O3",
    "so2": "SO2",
    "co": "CO",
}


def _send_extended_data(message: types.Message, lat: float, lon: float) -> None:
    try:
        weather = get_current_weather(lat, lon)
        components = get_air_pollution(lat, lon)
        analysis = analyze_air_pollution(components, extended=True)
    except Exception as e:
        logger.warning("Extended data request failed: %s", e)
        bot.reply_to(message, "Не удалось получить данные, попробуйте позже.")
        return
    blocks = []
    if weather and isinstance(weather, dict):
        blocks.append("Погода:\n" + _format_current_weather(weather))
    else:
        blocks.append("Погода:\nДанные по погоде временно недоступны.")
    # Качество воздуха
    status = (analysis.get("status") or "").strip()
    if status == "нет данных":
        blocks.append("Качество воздуха:\nДанные по качеству воздуха временно недоступны.")
    else:
        blocks.append("Качество воздуха:\n" + (status or "—"))

    details = analysis.get("details") or {}
    if details:
        detail_lines = []
        for key, info in details.items():
            if not isinstance(info, dict):
                continue
            label = _COMPONENT_LABELS.get(key, key.upper().replace("_", "."))
            val = info.get("value")
            st = info.get("status") or "—"
            val_s = f"{val} мкг/м³" if val is not None else "—"
            detail_lines.append(f"{label}: {val_s} — {st}")
        if detail_lines:
            blocks.append("Детали:\n" + "\n".join(detail_lines))

    try:
        text = "\n\n".join(blocks)
        bot.reply_to(message, text)
    except Exception as e:
        logger.warning("Send extended data failed: %s", e)
        bot.reply_to(message, "Не удалось получить данные, попробуйте позже.")


def _group_forecast_by_day(lst: list) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for item in lst or []:
        dt_txt = (item.get("dt_txt") or "").strip()
        if len(dt_txt) >= 10:
            day_key = dt_txt[:10]
            grouped.setdefault(day_key, []).append(item)
    return dict(sorted(grouped.items()))


def _day_label(day_key: str, index: int) -> str:
    if index == 0:
        return "Сегодня"
    if index == 1:
        return "Завтра"
    try:
        d = datetime.strptime(day_key, "%Y-%m-%d").date()
        return d.strftime("%d.%m")
    except (ValueError, TypeError):
        return day_key


def _build_forecast_days_keyboard(grouped: dict[str, list]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for i, day_key in enumerate(grouped.keys()):
        label = _day_label(day_key, i)
        markup.add(types.InlineKeyboardButton(label, callback_data=f"forecast:{day_key}"))
    return markup


def _format_forecast_day_slots(slots: list) -> str:
    lines = []
    for item in slots:
        dt_txt = (item.get("dt_txt") or "")[:16]
        time_part = dt_txt[11:16] if len(dt_txt) >= 16 else "—"
        main = item.get("main") or {}
        temp = main.get("temp")
        temp_s = f"{temp:.0f}°C" if temp is not None else "—"
        weather_list = item.get("weather") or []
        raw_desc = (weather_list[0].get("description") or "—") if weather_list else "—"
        desc = localize_weather_description(raw_desc)
        lines.append(f"{time_part}  {temp_s}  {desc}")
    return "\n".join(lines) if lines else "Нет данных за этот день."


def _forecast_back_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="forecast:back"))
    return markup


def _send_forecast_days_choice(message: types.Message, user_id: int, lat: float, lon: float) -> None:
    try:
        lst = get_forecast_5d3h(lat, lon)
    except Exception as e:
        logger.warning("Forecast request failed: %s", e)
        bot.reply_to(message, "Не удалось получить данные, попробуйте позже.")
        return
    if lst is None:
        bot.reply_to(message, "Не удалось получить данные, попробуйте позже.")
        return
    grouped = _group_forecast_by_day(lst)
    if not grouped:
        bot.reply_to(message, "Не удалось получить данные, попробуйте позже.")
        return
    user_forecasts[user_id] = grouped
    markup = _build_forecast_days_keyboard(grouped)
    bot.reply_to(message, "Выберите день прогноза", reply_markup=markup)


def _inline_weather_fallback_result() -> list:
    return [
        types.InlineQueryResultArticle(
            id="err",
            title="Нет данных",
            description="Город не найден / данные недоступны",
            input_message_content=types.InputTextMessageContent(
                message_text="Город не найден / данные недоступны.",
            ),
        ),
    ]


@bot.inline_handler(func=lambda q: True)
def inline_weather(inline_query: types.InlineQuery) -> None:
    """Inline-режим: по запросу (название города) — погода и ссылка на прогноз."""
    try:
        q = (inline_query.query or "").strip()
        if not q:
            bot.answer_inline_query(inline_query.id, [])
            return
        coords = get_coordinates(q)
        if coords is None:
            bot.answer_inline_query(inline_query.id, _inline_weather_fallback_result())
            return
        lat, lon = coords
        data = get_current_weather(lat, lon)
        if data is None or not isinstance(data, dict):
            bot.answer_inline_query(inline_query.id, _inline_weather_fallback_result())
            return
        name = data.get("name") or q
        main = data.get("main") or {}
        temp = main.get("temp")
        weather_list = data.get("weather") or []
        raw_desc = (weather_list[0].get("description") or "—") if weather_list else "—"
        desc = localize_weather_description(raw_desc)
        desc_short = f"{temp:.0f}°C" if temp is not None else "—"
        desc_short += f" / {desc}"
        if len(desc_short) > 255:
            desc_short = desc_short[:252] + "..."
        msg_text = _format_inline_weather_message(data)
        result = types.InlineQueryResultArticle(
            id=q[:64].replace(" ", "_"),
            title=name,
            description=desc_short,
            input_message_content=types.InputTextMessageContent(message_text=msg_text),
        )
        bot.answer_inline_query(inline_query.id, [result])
    except Exception as e:
        logger.warning("inline_weather failed: %s", e)
        try:
            bot.answer_inline_query(inline_query.id, _inline_weather_fallback_result())
        except Exception:
            pass


WELCOME_TEXT = """👋 Добро пожаловать в WeatherBot!

Я помогу вам получить актуальную информацию о погоде:
☀️ Текущая погода в любом городе
📅 Прогноз на 5 дней вперёд
📍 Погода по вашему местоположению
🔔 Погодные уведомления
📊 Сравнение погоды в разных городах
🌐 Расширенная информация о погоде

Выберите действие из меню ниже:"""


@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message) -> None:
    maybe_send_notification(message)
    user_id = message.from_user.id
    load_user(user_id)
    bot.reply_to(message, WELCOME_TEXT, reply_markup=build_main_keyboard())


@bot.message_handler(
    func=lambda m: m.content_type == "text"
    and m.from_user
    and (pending_city.get(m.from_user.id) or pending_extended.get(m.from_user.id))
)
def on_pending_city_or_extended(message: types.Message) -> None:
    maybe_send_notification(message)
    user_id = message.from_user.id
    city = (message.text or "").strip()
    if not city:
        bot.reply_to(message, "Введите название города.")
        return
    coords = get_coordinates(city)
    if coords is None:
        bot.reply_to(message, "Город не найден.")
        return
    lat, lon = coords
    if pending_city.get(user_id):
        pending_city.pop(user_id, None)
        user = load_user(user_id)
        user["city"] = city
        user["lat"] = lat
        user["lon"] = lon
        save_user(user_id, user)
        _send_current_weather(message, lat, lon)
    else:
        pending_extended.pop(user_id, None)
        _send_extended_data(message, lat, lon)


@bot.message_handler(
    func=lambda m: m.content_type == "text"
    and (m.from_user and pending_compare.get(m.from_user.id))
)
def on_pending_compare_message(message: types.Message) -> None:
    """Обработка ввода двух городов для сравнения погоды."""
    maybe_send_notification(message)
    user_id = message.from_user.id
    raw = (message.text or "").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    cities = parts[:2]
    if len(cities) < 2:
        bot.reply_to(message, "Нужно два города. Введите через запятую, например: Москва, Санкт-Петербург")
        return
    w = 22
    header = "Город".ljust(w) + " | Температура | Описание"
    rows = [header]
    for city_name in cities:
        coords = get_coordinates(city_name)
        if coords is None:
            rows.append(f"{city_name[:w].ljust(w)} | —            | Город не найден")
            continue
        lat, lon = coords
        try:
            data = get_current_weather(lat, lon)
        except Exception:
            data = None
        if not data or not isinstance(data, dict):
            rows.append(f"{city_name[:w].ljust(w)} | —            | Не удалось получить данные")
            continue
        main = data.get("main") or {}
        temp = main.get("temp")
        temp_s = f"{temp:+.0f}°C" if temp is not None else "—"
        weather_list = data.get("weather") or []
        desc = (weather_list[0].get("description") or "—") if weather_list else "—"
        rows.append(f"{city_name[:w].ljust(w)} | {temp_s.ljust(12)} | {desc}")
    del pending_compare[user_id]
    bot.reply_to(message, "\n".join(rows))


@bot.message_handler(func=lambda m: m.content_type == "text" and _get_menu_action((m.text or "").strip()) == "current_weather")
def on_current_weather(message: types.Message) -> None:
    """Текущая погода: всегда запрашиваем город (меню всегда активно)."""
    maybe_send_notification(message)
    user_id = message.from_user.id
    pending_city[user_id] = True
    bot.reply_to(message, "Введите название города.")


@bot.callback_query_handler(func=lambda c: (c.data or "").startswith("forecast:"))
def on_forecast_callback(callback: types.CallbackQuery) -> None:
    """Обработка выбора дня прогноза и кнопки «Назад»."""
    data = (callback.data or "").strip()
    user_id = callback.from_user.id if callback.from_user else 0
    grouped = user_forecasts.get(user_id) if user_id else None

    def answer_ok():
        try:
            bot.answer_callback_query(callback.id)
        except Exception:
            pass

    def edit_or_fail(text: str, markup: types.InlineKeyboardMarkup | None = None):
        try:
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=markup,
            )
        except Exception:
            try:
                bot.send_message(callback.message.chat.id, text, reply_markup=markup)
            except Exception:
                pass

    if grouped is None or not grouped:
        answer_ok()
        edit_or_fail("Прогноз устарел, запросите заново.")
        return

    if data == "forecast:back":
        answer_ok()
        edit_or_fail("Выберите день прогноза", _build_forecast_days_keyboard(grouped))
        return

    day_key = data[9:].strip() if len(data) > 9 else ""
    slots = grouped.get(day_key) if day_key else None
    if not slots:
        answer_ok()
        edit_or_fail("Прогноз устарел, запросите заново.")
        return

    try:
        text = _format_forecast_day_slots(slots)
    except Exception:
        text = "Не удалось сформировать прогноз за этот день."
    answer_ok()
    edit_or_fail(text, _forecast_back_keyboard())


@bot.callback_query_handler(func=lambda c: (c.data or "").startswith("notif:"))
def on_notif_callback(callback: types.CallbackQuery) -> None:
    """Включение/выключение уведомлений и выбор интервала."""
    data = (callback.data or "").strip()
    user_id = callback.from_user.id if callback.from_user else 0
    chat_id = callback.message.chat.id
    msg_id = callback.message.message_id

    try:
        bot.answer_callback_query(callback.id)
    except Exception:
        pass

    if data == "notif:on":
        try:
            bot.edit_message_text(
                "Выберите интервал (часы):",
                chat_id,
                msg_id,
                reply_markup=_build_notif_interval_keyboard(),
            )
        except Exception:
            try:
                bot.send_message(chat_id, "Выберите интервал (часы):", reply_markup=_build_notif_interval_keyboard())
            except Exception:
                pass
        return

    if data == "notif:off":
        try:
            user = load_user(user_id)
            n = user.setdefault("notifications", {})
            n["enabled"] = False
            n["last_sent"] = None
            save_user(user_id, user)
            bot.edit_message_text("Уведомления выключены.", chat_id, msg_id)
        except Exception:
            try:
                bot.send_message(chat_id, "Уведомления выключены.")
            except Exception:
                pass
        return

    if data.startswith("notif:int:"):
        try:
            hours_str = data[10:].strip()
            interval_h = int(hours_str) if hours_str else 1
            if interval_h < 1:
                interval_h = 1
            if interval_h > 24:
                interval_h = 24
        except (ValueError, TypeError):
            interval_h = 1
        try:
            user = load_user(user_id)
            n = user.setdefault("notifications", {})
            n["enabled"] = True
            n["interval_h"] = interval_h
            n["last_sent"] = None
            save_user(user_id, user)
            bot.edit_message_text(f"Уведомления включены каждые {interval_h} ч.", chat_id, msg_id)
        except Exception:
            try:
                bot.send_message(chat_id, f"Уведомления включены каждые {interval_h} ч.")
            except Exception:
                pass


@bot.message_handler(content_types=["location"])
def handle_location(message: types.Message) -> None:
    """Принимает геолокацию, сохраняет координаты и подтверждает пользователю."""
    maybe_send_notification(message)
    loc = message.location
    if not loc:
        return
    try:
        lat = float(loc.latitude)
        lon = float(loc.longitude)
    except (TypeError, ValueError):
        bot.reply_to(message, "Не удалось прочитать координаты.")
        return
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        bot.reply_to(message, "Некорректные координаты.")
        return
    user_id = message.from_user.id
    user = load_user(user_id)
    user["city"] = "Моя геолокация"
    user["lat"] = lat
    user["lon"] = lon
    save_user(user_id, user)
    bot.reply_to(
        message,
        "Геолокация сохранена, теперь могу показывать погоду по вашему местоположению.",
    )


@bot.message_handler(func=lambda m: True)
def route_message(message: types.Message) -> None:
    try:
        maybe_send_notification(message)
        text = (message.text or "").strip()
        user_id = message.from_user.id
        user = load_user(user_id)
        action = _get_menu_action(text)
        if action == "forecast":
            if not _has_valid_coords(user):
                _ask_for_location(message)
            else:
                _send_forecast_days_choice(message, user_id, float(user["lat"]), float(user["lon"]))
        elif action == "compare":
            pending_compare[user_id] = True
            bot.reply_to(
                message,
                "Введите два города через запятую (пример: Москва, Санкт-Петербург)",
            )
        elif action == "extended":
            pending_extended[user_id] = True
            bot.reply_to(message, "Введите название города.")
        elif action == "notifications":
            bot.reply_to(message, "🔔 Уведомления о погоде:", reply_markup=_build_notif_on_off_keyboard())
        else:
            bot.reply_to(message, "Выберите пункт из меню ниже 👇", reply_markup=build_main_keyboard())
    except Exception as e:
        logger.exception("route_message failed")
        try:
            bot.reply_to(message, "Не удалось получить данные, попробуйте позже.")
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(name)s: %(message)s")
    bot.infinity_polling()
