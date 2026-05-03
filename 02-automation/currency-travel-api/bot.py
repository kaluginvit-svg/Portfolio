# -*- coding: utf-8 -*-
"""
Telegram-бот: мини-кошелёк для путешественника.
API: api.exchangerate.host/convert. Все запросы через current_api.
"""

import os
from decimal import Decimal, InvalidOperation

import telebot
from dotenv import load_dotenv

import current_api
import currencies
import database

load_dotenv()
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise SystemExit("Задайте TELEGRAM_BOT_TOKEN в .env")

bot = telebot.TeleBot(BOT_TOKEN)
database.init_db()

# Состояния диалога: user_id -> {"state": str, ...}
user_state: dict[int, dict] = {}

# Callback data prefixes
CB_MAIN = "main"
CB_NEWTRIP = "newtrip"
CB_MYTRIPS = "mytrips"
CB_BALANCE = "balance"
CB_HISTORY = "history"
CB_SETRATE = "setrate"
CB_TRIP = "trip:"
CB_EXPENSE_YES = "exp_yes:"
CB_EXPENSE_NO = "exp_no:"
CB_RATE_OK = "rate_ok"
CB_RATE_NO = "rate_no"


def set_state(uid: int, state: str, **kwargs):
    user_state[uid] = {"state": state, **kwargs}


def get_state(uid: int) -> dict | None:
    return user_state.get(uid)


def clear_state(uid: int):
    user_state.pop(uid, None)


def main_menu_keyboard():
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        telebot.types.InlineKeyboardButton("🧳 Создать путешествие", callback_data=CB_NEWTRIP),
        telebot.types.InlineKeyboardButton("📋 Мои путешествия", callback_data=CB_MYTRIPS),
    ).add(
        telebot.types.InlineKeyboardButton("💰 Баланс", callback_data=CB_BALANCE),
        telebot.types.InlineKeyboardButton("📜 История расходов", callback_data=CB_HISTORY),
    ).add(
        telebot.types.InlineKeyboardButton("💱 Изменить курс", callback_data=CB_SETRATE),
    )
    return kb


def send_main_menu(chat_id: int, text: str = "📌 Главное меню:"):
    bot.send_message(chat_id, text, reply_markup=main_menu_keyboard())


def trip_title(t: dict) -> str:
    return f"✈️ {t['from_country']} → {t['to_country']}"


def format_balance(t: dict) -> str:
    return database.format_balance(
        t["balance_dest"], t["balance_home"],
        t["to_currency"], t["from_currency"],
    )


# ——— Команды и старт ———

@bot.message_handler(commands=["start"])
def cmd_start(msg: telebot.types.Message):
    uid = msg.from_user.id
    database.ensure_user(uid)
    clear_state(uid)
    bot.send_message(
        msg.chat.id,
        "👋 Привет! Я мини-кошелёк для путешествий 💳\n"
        "Курсы валют — через api.exchangerate.host.\n\n"
        "🧳 Создайте путешествие: укажите страну вылета и назначения — я покажу курс и помогу вести баланс в двух валютах.\n\n"
        "💸 Любое сообщение с числом — сумма расхода в валюте страны пребывания.",
        reply_markup=main_menu_keyboard(),
    )


@bot.message_handler(commands=["newtrip"])
def cmd_newtrip(msg: telebot.types.Message):
    set_state(msg.from_user.id, "from_country")
    bot.send_message(msg.chat.id, "🌍 Введите страну отправления (например: Россия, USA):")


@bot.message_handler(commands=["switch"])
def cmd_switch(msg: telebot.types.Message):
    uid = msg.from_user.id
    trips = database.get_user_trips(uid)
    if not trips:
        bot.send_message(msg.chat.id, "📭 У вас пока нет путешествий. Создайте первое!", reply_markup=main_menu_keyboard())
        return
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for t in trips:
        keyboard.add(telebot.types.InlineKeyboardButton(
            trip_title(t) + (" ✅" if database.get_active_trip_id(uid) == t["id"] else ""),
            callback_data=CB_TRIP + str(t["id"]),
        ))
    bot.send_message(msg.chat.id, "📋 Выберите путешествие:", reply_markup=keyboard)


@bot.message_handler(commands=["balance"])
def cmd_balance(msg: telebot.types.Message):
    show_balance(msg.from_user.id, msg.chat.id)


@bot.message_handler(commands=["history"])
def cmd_history(msg: telebot.types.Message):
    show_history(msg.from_user.id, msg.chat.id)


@bot.message_handler(commands=["setrate"])
def cmd_setrate(msg: telebot.types.Message):
    uid = msg.from_user.id
    trip_id = database.get_active_trip_id(uid)
    if not trip_id:
        bot.send_message(msg.chat.id, "⚠️ Сначала выберите или создайте путешествие.", reply_markup=main_menu_keyboard())
        return
    trip = database.get_trip(trip_id, uid)
    if not trip:
        return
    set_state(uid, "set_rate", trip_id=trip_id)
    bot.send_message(
        msg.chat.id,
        f"💱 Текущий курс: 1 {trip['to_currency']} = {trip['rate']:.4f} {trip['from_currency']}\n"
        "Введите новый курс (одно число, например 12.5):",
    )


def show_balance(uid: int, chat_id: int):
    trip_id = database.get_active_trip_id(uid)
    if not trip_id:
        bot.send_message(chat_id, "⚠️ Нет активного путешествия. Создайте или выберите его.", reply_markup=main_menu_keyboard())
        return
    trip = database.get_trip(trip_id, uid)
    if not trip:
        return
    grouped = database.get_expenses_grouped_by_purpose(trip_id, uid)
    breakdown = database.format_balance_breakdown(grouped, trip["to_currency"], trip["from_currency"])
    msg = (
        f"🗺️ Путешествие: {trip_title(trip)}\n💰 Остаток: {format_balance(trip)}"
    )
    if breakdown:
        msg += f"\n\n📋 Расходы по назначению:\n{breakdown}"
    msg += f"\n\n💡 Чтобы учесть расход — введите сумму в {trip['to_currency']}."
    bot.send_message(chat_id, msg, reply_markup=main_menu_keyboard())


def show_history(uid: int, chat_id: int):
    trip_id = database.get_active_trip_id(uid)
    if not trip_id:
        bot.send_message(chat_id, "⚠️ Нет активного путешествия.", reply_markup=main_menu_keyboard())
        return
    trip = database.get_trip(trip_id, uid)
    if not trip:
        return
    expenses = database.get_expenses(trip_id, uid)
    if not expenses:
        bot.send_message(chat_id, "📜 История расходов пуста.", reply_markup=main_menu_keyboard())
        return
    lines = []
    for e in expenses:
        purpose = (e.get("purpose") or "").strip() or "—"
        dt = (e.get("created_at") or "")[:16].replace("T", " ")
        lines.append(f"• {e['amount_dest']:.2f} {trip['to_currency']} = {e['amount_home']:.2f} {trip['from_currency']} — {purpose} ({dt})")
    bot.send_message(
        chat_id,
        "📜 История расходов:\n" + "\n".join(lines[:30]),
        reply_markup=main_menu_keyboard(),
    )


# ——— Inline callbacks ———

@bot.callback_query_handler(func=lambda c: c.data == CB_MAIN)
def cb_main(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    try:
        bot.edit_message_text("📌 Главное меню:", c.message.chat.id, c.message.message_id, reply_markup=main_menu_keyboard())
    except Exception:
        bot.send_message(c.message.chat.id, "📌 Главное меню:", reply_markup=main_menu_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == CB_NEWTRIP)
def cb_newtrip(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    set_state(c.from_user.id, "from_country")
    bot.send_message(c.message.chat.id, "🌍 Введите страну отправления (например: Россия, USA):")


@bot.callback_query_handler(func=lambda c: c.data == CB_MYTRIPS)
def cb_mytrips(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    uid = c.from_user.id
    trips = database.get_user_trips(uid)
    if not trips:
        bot.send_message(c.message.chat.id, "📭 У вас пока нет путешествий. Создайте первое!", reply_markup=main_menu_keyboard())
        return
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for t in trips:
        keyboard.add(telebot.types.InlineKeyboardButton(
            trip_title(t) + (" ✅" if database.get_active_trip_id(uid) == t["id"] else ""),
            callback_data=CB_TRIP + str(t["id"]),
        ))
    keyboard.add(telebot.types.InlineKeyboardButton("🏠 Главное меню", callback_data=CB_MAIN))
    try:
        bot.edit_message_text("📋 Выберите путешествие:", c.message.chat.id, c.message.message_id, reply_markup=keyboard)
    except Exception:
        bot.send_message(c.message.chat.id, "📋 Выберите путешествие:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data.startswith(CB_TRIP))
def cb_trip(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    uid = c.from_user.id
    trip_id = int(c.data.split(":")[1])
    trip = database.get_trip(trip_id, uid)
    if not trip:
        bot.send_message(c.message.chat.id, "❌ Путешествие не найдено.", reply_markup=main_menu_keyboard())
        return
    database.set_active_trip(uid, trip_id)
    bot.send_message(
        c.message.chat.id,
        f"✅ Активно: {trip_title(trip)}\n💰 Баланс: {format_balance(trip)}\n\n"
        f"💡 Вводите суммы расходов в {trip['to_currency']} — я переведу в {trip['from_currency']} и предложу учесть.",
        reply_markup=main_menu_keyboard(),
    )


@bot.callback_query_handler(func=lambda c: c.data == CB_BALANCE)
def cb_balance(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    show_balance(c.from_user.id, c.message.chat.id)


@bot.callback_query_handler(func=lambda c: c.data == CB_HISTORY)
def cb_history(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    show_history(c.from_user.id, c.message.chat.id)


@bot.callback_query_handler(func=lambda c: c.data == CB_SETRATE)
def cb_setrate(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    uid = c.from_user.id
    trip_id = database.get_active_trip_id(uid)
    if not trip_id:
        bot.send_message(c.message.chat.id, "⚠️ Сначала выберите путешествие.", reply_markup=main_menu_keyboard())
        return
    trip = database.get_trip(trip_id, uid)
    if not trip:
        return
    set_state(uid, "set_rate", trip_id=trip_id)
    bot.send_message(
        c.message.chat.id,
        f"💱 Текущий курс: 1 {trip['to_currency']} = {trip['rate']:.4f} {trip['from_currency']}\n"
        "Введите новый курс (одно число, например 12.5):",
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith(CB_EXPENSE_YES))
def cb_expense_yes(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    uid = c.from_user.id
    payload = c.data.replace(CB_EXPENSE_YES, "")
    parts = payload.split(":")
    if len(parts) != 2:
        return
    try:
        amount_dest = float(parts[0])
        amount_home = float(parts[1])
    except ValueError:
        return
    trip_id = database.get_active_trip_id(uid)
    if not trip_id:
        return
    trip = database.get_trip(trip_id, uid)
    if not trip:
        return
    st = get_state(uid)
    purpose = (st.get("purpose") or "").strip() if st else ""
    database.add_expense(trip_id, uid, amount_dest, amount_home, purpose=purpose)
    clear_state(uid)
    trip = database.get_trip(trip_id, uid)
    bot.send_message(
        c.message.chat.id,
        f"✅ Расход учтён. 💰 Остаток: {format_balance(trip)}",
        reply_markup=main_menu_keyboard(),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith(CB_EXPENSE_NO))
def cb_expense_no(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    clear_state(c.from_user.id)
    bot.send_message(c.message.chat.id, "❌ Расход не учтён.", reply_markup=main_menu_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == CB_RATE_OK)
def cb_rate_ok(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    uid = c.from_user.id
    st = get_state(uid)
    if not st or st.get("state") != "rate_confirm":
        return
    set_state(uid, "initial_amount", from_currency=st["from_currency"], to_currency=st["to_currency"], from_country=st["from_country"], to_country=st["to_country"], rate=st["rate"])
    bot.send_message(
        c.message.chat.id,
        "💵 Введите начальную сумму в домашней валюте (в которой вы выезжаете).\n\n"
        "💡 Я переведу её в валюту страны пребывания по выбранному курсу — баланс будет в обеих валютах.",
    )


@bot.callback_query_handler(func=lambda c: c.data == CB_RATE_NO)
def cb_rate_no(c: telebot.types.CallbackQuery):
    bot.answer_callback_query(c.id)
    uid = c.from_user.id
    st = get_state(uid)
    if not st or st.get("state") != "rate_confirm":
        return
    set_state(uid, "manual_rate", from_currency=st["from_currency"], to_currency=st["to_currency"], from_country=st["from_country"], to_country=st["to_country"])
    bot.send_message(
        c.message.chat.id,
        "💱 Введите курс вручную: сколько единиц домашней валюты ({0}) за 1 {1}.\n"
        "Пример: 12.5 значит 1 {1} = 12.5 {0}.".format(st["from_currency"], st["to_currency"]),
    )


# ——— Обработка текста по состояниям ———

def parse_number(text: str) -> float | None:
    text = (text or "").strip().replace(",", ".")
    try:
        return float(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


@bot.message_handler(func=lambda m: True)
def on_message(msg: telebot.types.Message):
    uid = msg.from_user.id
    chat_id = msg.chat.id
    text = (msg.text or "").strip()
    st = get_state(uid)

    # Состояние: ввод страны отправления
    if st and st.get("state") == "from_country":
        from_cur = currencies.country_to_currency(text)
        if not from_cur:
            bot.send_message(chat_id, "⚠️ Не удалось определить валюту по этой стране. Введите ещё раз (например: Россия, USA, Китай):")
            return
        set_state(uid, "to_country", from_country=text, from_currency=from_cur)
        bot.send_message(
            chat_id,
            f"✅ Страна отправления: {text}. Валюта: {from_cur}.\n\n"
            "🌍 Теперь введите страну назначения (например: Китай, Thailand):",
        )
        return

    # Состояние: ввод страны назначения
    if st and st.get("state") == "to_country":
        to_cur = currencies.country_to_currency(text)
        if not to_cur:
            bot.send_message(chat_id, "⚠️ Не удалось определить валюту. Введите страну назначения ещё раз:")
            return
        from_cur = st["from_currency"]
        from_country = st["from_country"]
        to_country = text
        if from_cur == to_cur:
            bot.send_message(chat_id, "⚠️ Валюта отправления и назначения совпадают. Введите другую страну:")
            return
        # Курс через API: только endpoint /convert. 1 to_cur = rate from_cur
        conv = current_api.convert_currency(1.0, to_cur, from_cur)
        if not conv.get("success") or "result" not in conv:
            err = (conv.get("error") or {}).get("info", "Неизвестная ошибка API")
            bot.send_message(chat_id, f"⚠️ Не удалось получить курс для этой пары валют. {err}", reply_markup=main_menu_keyboard())
            clear_state(uid)
            return
        rate = float(conv["result"])
        set_state(uid, "rate_confirm", from_currency=from_cur, to_currency=to_cur, from_country=from_country, to_country=to_country, rate=rate)
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2).add(
            telebot.types.InlineKeyboardButton("✅ Да, подходит", callback_data=CB_RATE_OK),
            telebot.types.InlineKeyboardButton("✏️ Нет, ввести вручную", callback_data=CB_RATE_NO),
        )
        bot.send_message(
            chat_id,
            f"✅ Страна назначения: {to_country}. Валюта: {to_cur}.\n\n"
            f"💱 Курс по API: 1 {to_cur} = {rate:.4f} {from_cur}\n"
            "Если в обменнике другой курс — нажмите «Нет» и введите свой.\n\nПодходит этот курс?",
            reply_markup=keyboard,
        )
        return

    # Ручной ввод курса
    if st and st.get("state") == "manual_rate":
        rate = parse_number(text)
        if rate is None or rate <= 0:
            bot.send_message(chat_id, "⚠️ Введите положительное число (курс):")
            return
        set_state(uid, "initial_amount", from_currency=st["from_currency"], to_currency=st["to_currency"], from_country=st["from_country"], to_country=st["to_country"], rate=rate)
        bot.send_message(chat_id, "💵 Введите начальную сумму в домашней валюте. Она будет переведена в валюту страны пребывания по вашему курсу.")
        return

    # Начальная сумма в домашней валюте
    if st and st.get("state") == "initial_amount":
        amount_home = parse_number(text)
        if amount_home is None or amount_home < 0:
            bot.send_message(chat_id, "⚠️ Введите положительное число (сумма в домашней валюте):")
            return
        rate = st["rate"]
        amount_dest = amount_home / rate
        database.create_trip(
            uid,
            st["from_country"],
            st["to_country"],
            st["from_currency"],
            st["to_currency"],
            rate,
            amount_dest,
            amount_home,
        )
        clear_state(uid)
        bot.send_message(
            chat_id,
            f"✅ Путешествие создано!\n💰 Баланс: {amount_dest:.2f} {st['to_currency']} = {amount_home:.2f} {st['from_currency']}\n\n"
            "💡 Теперь можно просто вводить суммы расходов в валюте страны пребывания — я переведу их в домашнюю и предложу учесть. Например, введите 100 для расхода в 100 {0}.".format(st["to_currency"]),
            reply_markup=main_menu_keyboard(),
        )
        return

    # Изменение курса
    if st and st.get("state") == "set_rate":
        rate = parse_number(text)
        if rate is None or rate <= 0:
            bot.send_message(chat_id, "⚠️ Введите положительное число (курс):")
            return
        trip_id = st["trip_id"]
        if database.update_trip_rate(trip_id, uid, rate):
            trip = database.get_trip(trip_id, uid)
            bot.send_message(chat_id, f"✅ Курс обновлён. 💰 Баланс: {format_balance(trip)}", reply_markup=main_menu_keyboard())
        else:
            bot.send_message(chat_id, "❌ Не удалось обновить курс.", reply_markup=main_menu_keyboard())
        clear_state(uid)
        return

    # Назначение расхода (текст после ввода суммы)
    if st and st.get("state") == "expense_purpose":
        purpose = (text or "—").strip()[:200]
        set_state(uid, "expense_confirm", amount_dest=st["amount_dest"], amount_home=st["amount_home"], purpose=purpose)
        trip_id = database.get_active_trip_id(uid)
        trip = database.get_trip(trip_id, uid) if trip_id else None
        if not trip:
            clear_state(uid)
            send_main_menu(chat_id, "⚠️ Путешествие не найдено.")
            return
        to_cur, from_cur = trip["to_currency"], trip["from_currency"]
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2).add(
            telebot.types.InlineKeyboardButton("✅ Учесть расход", callback_data=CB_EXPENSE_YES + f"{st['amount_dest']}:{st['amount_home']}"),
            telebot.types.InlineKeyboardButton("❌ Нет", callback_data=CB_EXPENSE_NO),
        )
        bot.send_message(
            chat_id,
            f"💸 {st['amount_dest']} {to_cur} = {st['amount_home']:.2f} {from_cur} — {purpose}\n\nУчесть как расход?",
            reply_markup=keyboard,
        )
        return

    # Подтверждение расхода (ожидаем только callback, не текст)
    if st and st.get("state") == "expense_confirm":
        send_main_menu(chat_id, "💬 Ответьте на вопрос о расходе кнопками выше или введите число для нового расхода.")
        return

    # Число — трактуем как расход в валюте страны пребывания
    num = parse_number(text)
    if num is not None and num > 0:
        trip_id = database.get_active_trip_id(uid)
        if not trip_id:
            send_main_menu(chat_id, "⚠️ Нет активного путешествия. Создайте или выберите его.")
            return
        trip = database.get_trip(trip_id, uid)
        if not trip:
            return
        to_cur = trip["to_currency"]
        from_cur = trip["from_currency"]
        amount_dest = num
        conv = current_api.convert_currency(amount_dest, to_cur, from_cur)
        if not conv.get("success") or "result" not in conv:
            bot.send_message(chat_id, "⚠️ Не удалось пересчитать сумму по курсу API. Попробуйте позже.")
            return
        amount_home = float(conv["result"])
        if amount_dest > trip["balance_dest"]:
            bot.send_message(chat_id, f"⚠️ Сумма больше баланса ({format_balance(trip)}). Введите меньшую сумму.")
            return
        set_state(uid, "expense_purpose", amount_dest=amount_dest, amount_home=amount_home)
        bot.send_message(chat_id, f"💸 {amount_dest} {to_cur} = {amount_home:.2f} {from_cur}\n\n📝 Введите назначение расхода (текст, например: обед, такси, сувениры):")
        return

    send_main_menu(chat_id, "💸 Введите число для расхода или выберите действие в меню.")


if __name__ == "__main__":
    bot.infinity_polling()
