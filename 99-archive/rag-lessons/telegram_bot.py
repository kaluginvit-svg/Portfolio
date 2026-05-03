"""Telegram + RAGAgent: эмбеддинги по URL, поиск, профиль и меню команд (персонализация).

Запуск: .\\venv\\Scripts\\python.exe telegram_bot.py
"""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

import telebot
from dotenv import load_dotenv
from telebot import types

from rag_agent import RAGAgent
from user_store import get_store

load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
_log = logging.getLogger("telegram_bot")

_STANDALONE_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)

_agent: RAGAgent | None = None

HELP_TEXT = """📋 Доступные команды

🔍 Поиск и вопросы
Просто напиши вопрос — я найду ответ в базе знаний.
/search <запрос> — поиск по базе данных (выдача релевантных чанков).

🗂️ Управление знаниями
/add_url <URL> — добавить страницу в базу знаний
/add_text <текст> — добавить текст в базу знаний
Или одной строкой только https://… — то же, что add_url.

👤 Профиль
/profile — посмотреть свой профиль
/summary — краткое резюме о вас
/suggestions — предложения вопросов для изучения
/engagement — уровень вашей активности
/forget_me — удалить локальный профиль и заметки о себе

ℹ️ Другое
/help — это сообщение
/remember <текст> — запомнить в Pinecone и в профиль
/cat — демо GET (коты)

💡 Заметки из /remember попадают в профиль и в векторную память — ответы могут быть персональнее."""

SUGGESTIONS_LIST = (
    "Что проверить в счёте от поставщика перед проведением?",
    "Как закрыть месяц без ошибок в первичке?",
    "Что делать при расхождении сумм между двумя таблицами?",
    "Как кратко объяснить руководителю отклонение факт/план?",
    "Какие поля чаще всего пропускают во входящем УПД?",
    "Как проверить таблицу на дубли и пропуски?",
    "Что написать клиенту по просроченной дебиторке?",
)


def get_agent() -> RAGAgent:
    global _agent
    if _agent is None:
        _agent = RAGAgent()
        _log.info("RAGAgent готов; recursion_limit=%s", _agent.recursion_limit())
    return _agent


def _tg_name(message: types.Message) -> str | None:
    u = message.from_user
    if not u:
        return None
    parts = [u.first_name or "", u.last_name or ""]
    return " ".join(p for p in parts if p).strip() or None


def bump_user(message: types.Message, *, increment: bool = True) -> None:
    uid = message.from_user.id if message.from_user else 0
    if not uid:
        return
    get_store().touch(uid, telegram_name=_tg_name(message), increment=increment)


def _strip_save_prefix(text: str) -> str | None:
    t = text.strip()
    m = re.match(r"^запомни\s*:\s*(.+)$", t, flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def _engagement_label(n: int) -> str:
    if n <= 0:
        return "🌱 только начали диалог"
    if n < 8:
        return "📎 активность ниже среднего"
    if n < 25:
        return "⚡ стабильное использование"
    if n < 60:
        return "🔥 высокая вовлечённость"
    return "🏆 очень высокая активность"


def _register_bot_menu(bot: telebot.TeleBot) -> None:
    menu = [
        types.BotCommand("start", "Начать"),
        types.BotCommand("help", "Все команды"),
        types.BotCommand("search", "Поиск по базе знаний"),
        types.BotCommand("add_url", "Добавить страницу по URL"),
        types.BotCommand("add_text", "Добавить текст в базу"),
        types.BotCommand("profile", "Мой профиль"),
        types.BotCommand("summary", "Краткое резюме о вас"),
        types.BotCommand("suggestions", "Идеи вопросов"),
        types.BotCommand("engagement", "Уровень активности"),
        types.BotCommand("forget_me", "Удалить данные профиля"),
        types.BotCommand("remember", "Запомнить фразу"),
        types.BotCommand("cat", "Случайный факт о котах"),
    ]
    try:
        if bot.set_my_commands(menu):
            _log.info("Меню команд: %s пунктов", len(menu))
        else:
            _log.warning("set_my_commands вернул False")
    except Exception:
        _log.exception("set_my_commands")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        sys.exit("Задай TELEGRAM_BOT_TOKEN в .env")

    bot = telebot.TeleBot(token, parse_mode=None)
    _register_bot_menu(bot)

    @bot.message_handler(commands=["start"])
    def on_start(message: types.Message) -> None:
        bump_user(message)
        bot.reply_to(
            message,
            "Привет! Я помогаю с базой знаний (Pinecone + RAG).\n\n"
            "• Отправь одну строку с https://… — страница попадёт в индекс.\n"
            "• Или напиши вопрос — поищу в базе и отвечу.\n"
            "• Команды — в меню слева или /help.\n\n"
            "💡 Часть данных профиля хранится локально (файл data/user_profiles.json).",
        )

    @bot.message_handler(commands=["help", "помощь"])
    def on_help(message: types.Message) -> None:
        bump_user(message)
        bot.reply_to(message, HELP_TEXT)

    @bot.message_handler(commands=["profile"])
    def on_profile(message: types.Message) -> None:
        bump_user(message, increment=False)
        uid = message.from_user.id if message.from_user else 0
        p = get_store().view(uid)
        name = p.telegram_name.strip() or "Не указано"
        notes = p.important_notes.strip() or "Пока не сохранено важной информации."
        text = (
            "👤 Твой профиль:\n\n"
            f"🆔 ID: {p.user_id}\n"
            f"👤 Имя: {name}\n"
            f"📅 Регистрация: {p.first_seen}\n"
            f"🕒 Последняя активность: {p.last_seen}\n\n"
            "🧠 Важная информация о тебе:\n"
            f"{notes}\n\n"
            f"💬 Сообщений в контексте: {p.message_count}"
        )
        bot.reply_to(message, text)

    @bot.message_handler(commands=["summary"])
    def on_summary(message: types.Message) -> None:
        bump_user(message, increment=False)
        p = get_store().view(message.from_user.id if message.from_user else 0)
        if p.important_notes.strip():
            body = p.important_notes.strip()[:1500]
        else:
            body = "Информация о пользователе пока не собрана."
        bot.reply_to(
            message,
            "📋 Краткое резюме о вас:\n\n"
            f"{body}\n\n"
            "🤖 Эта информация помогает мне давать более персонализированные ответы.",
        )

    @bot.message_handler(commands=["suggestions"])
    def on_suggestions(message: types.Message) -> None:
        bump_user(message)
        lines = "\n".join(f"• {s}" for s in SUGGESTIONS_LIST)
        bot.reply_to(message, f"💡 Можно спросить:\n\n{lines}")

    @bot.message_handler(commands=["engagement"])
    def on_engagement(message: types.Message) -> None:
        bump_user(message, increment=False)
        p = get_store().view(message.from_user.id if message.from_user else 0)
        tier = _engagement_label(p.message_count)
        bot.reply_to(
            message,
            f"📊 Активность\n\n"
            f"Сообщений учтено: {p.message_count}\n"
            f"{tier}\n\n"
            "Счётчик растёт при сообщениях к боту.",
        )

    @bot.message_handler(commands=["forget_me"])
    def on_forget_me(message: types.Message) -> None:
        uid = message.from_user.id if message.from_user else 0
        ok = get_store().forget(uid)
        if ok:
            bot.reply_to(
                message,
                "🗑 Локальный профиль и заметки удалены.\n"
                "Векторы в Pinecone с твоим `chat_id` при желании можно очистить отдельно в консоли Pinecone.",
            )
        else:
            bot.reply_to(message, "Записей о тебе в локальной базе не было.")

    @bot.message_handler(commands=["search"])
    def on_search(message: types.Message) -> None:
        bump_user(message)
        raw = (message.text or "").strip()
        parts = raw.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            bot.reply_to(message, "Формат: /search твой запрос по смыслу")
            return
        q = parts[1].strip()
        uid = message.from_user.id if message.from_user else 0
        _log.info("/search chat_id=%s user_id=%s query=%r", message.chat.id, uid, q[:240])
        bot.send_chat_action(message.chat.id, "typing")
        try:
            out = get_agent().retrieve(q)
        except Exception:
            _log.exception("retrieve")
            bot.reply_to(message, "Ошибка поиска в Pinecone.")
            return
        bot.reply_to(message, f"🔍 Результаты поиска:\n\n{out[:4000]}")

    @bot.message_handler(commands=["add_text"])
    def on_add_text(message: types.Message) -> None:
        bump_user(message)
        raw = (message.text or "").strip()
        parts = raw.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            bot.reply_to(message, "Формат: /add_text любой текст для индекса")
            return
        body = parts[1].strip()
        bot.send_chat_action(message.chat.id, "typing")
        try:
            cid = message.chat.id
            rid = get_agent().upsert_text_vector(
                body,
                metadata={
                    "phrase": body[:4000],
                    "text": body[:4000],
                    "source": "add_text",
                    "chat_id": str(cid),
                },
            )
        except Exception:
            _log.exception("add_text")
            bot.reply_to(message, "Не удалось записать текст в Pinecone.")
            return
        bot.reply_to(message, f"Добавлено в базу. id записи: {rid}")

    @bot.message_handler(commands=["add_url"])
    def on_add_url(message: types.Message) -> None:
        bump_user(message)
        raw = (message.text or "").strip()
        parts = raw.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            bot.reply_to(message, "Формат: /add_url https://example.com/page")
            return
        url = parts[1].strip()
        bot.send_chat_action(message.chat.id, "typing")
        try:
            msg = get_agent().index_url(url)
        except Exception:
            _log.exception("index_url")
            bot.reply_to(message, "Не удалось загрузить URL.")
            return
        bot.reply_to(message, msg[:4000])

    @bot.message_handler(commands=["cat"])
    def on_cat(message: types.Message) -> None:
        bump_user(message)
        bot.send_chat_action(message.chat.id, "typing")
        try:
            fact = RAGAgent.fetch_cat_fact_http()
        except Exception:
            _log.exception("cat_fact")
            bot.reply_to(message, "Не удалось достучаться до catfact.ninja.")
            return
        bot.reply_to(message, fact[:4000])

    @bot.message_handler(commands=["запомни", "remember"])
    def on_remember_cmd(message: types.Message) -> None:
        bump_user(message)
        raw = (message.text or "").strip()
        parts = raw.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            bot.reply_to(message, "Например: /remember номер договора 123/2025")
            return
        payload = parts[1].strip()
        uid = message.from_user.id if message.from_user else 0
        cid = message.chat.id
        try:
            mid = get_agent().save_user_memory(payload, chat_id=cid, user_id=uid)
            get_store().set_memory_note(uid, payload)
        except Exception:
            _log.exception("save_user_memory")
            bot.reply_to(message, "Ошибка записи в Pinecone.")
            return
        bot.reply_to(message, f"Сохранил в Pinecone и профиль: {mid}")

    @bot.message_handler(func=lambda m: m.text and _STANDALONE_URL.match(m.text.strip()))
    def on_standalone_url(message: types.Message) -> None:
        bump_user(message)
        url = (message.text or "").strip()
        bot.send_chat_action(message.chat.id, "typing")
        try:
            report = get_agent().index_url(url)
        except Exception:
            _log.exception("standalone index_url")
            bot.reply_to(message, "Не удалось обработать URL.")
            return
        bot.reply_to(
            message,
            "Готово (эмбеддинги → Pinecone).\n\n"
            + report[:3800]
            + "\n\nТеперь можно задать вопрос по смыслу страницы.",
        )

    @bot.message_handler(func=lambda m: m.text and _strip_save_prefix(m.text) is not None)
    def on_prefix_remember(message: types.Message) -> None:
        bump_user(message)
        inner = _strip_save_prefix(message.text or "") or ""
        if not inner:
            return
        uid = message.from_user.id if message.from_user else 0
        cid = message.chat.id
        try:
            mid = get_agent().save_user_memory(inner, chat_id=cid, user_id=uid)
            get_store().set_memory_note(uid, inner)
            bot.reply_to(message, f"Ок: {mid}")
        except Exception:
            _log.exception("prefix_remember")
            bot.reply_to(message, "Ошибка сохранения.")

    @bot.message_handler(content_types=["text"])
    def on_text(message: types.Message) -> None:
        text = (message.text or "").strip()
        if not text or text.startswith("/"):
            return
        bump_user(message)
        bot.send_chat_action(message.chat.id, "typing")
        try:
            ans = get_agent().run(text)
        except Exception:
            _log.exception("agent.run")
            bot.reply_to(message, "Ошибка агента. См. лог.")
            return
        ans = (ans or "").strip() or "Пустой ответ."
        if len(ans) > 4096:
            ans = ans[:4090] + "…"
        bot.reply_to(message, ans)

    _log.info("Polling telegram_bot.py…")
    bot.infinity_polling(skip_pending=True, interval=0, timeout=60)


if __name__ == "__main__":
    main()
