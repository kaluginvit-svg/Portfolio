"""
Telegram-бот: тот же агент, что и в CLI. Запуск из каталога agent/: python tg_bot.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    _d = Path(__file__).resolve().parent
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

_verbose_argv = "--verbose" in sys.argv or "-v" in sys.argv

from dotenv import load_dotenv
from log_config import get_trace_callback, setup_logging
import telebot
from telebot import types

from agent import build_executor, lc_history_from_pairs
from session_memory import (
    append_turn,
    get_chat_bucket,
    load_telegram_store,
    pairs_from_memory,
    save_telegram_store,
)

_AGENT_DIR = Path(__file__).resolve().parent
load_dotenv(_AGENT_DIR / ".env")
setup_logging(_AGENT_DIR, verbose=_verbose_argv)

_log = logging.getLogger("local_agent.telegram")
_trace = get_trace_callback()

TG_MEMORY_FILE = _AGENT_DIR / "telegram_memory.json"
TELEGRAM_CHUNK = 4000


def _send_long(bot: telebot.TeleBot, chat_id: int, text: str, reply_to: int | None = None) -> None:
    t = text or ""
    if not t.strip():
        bot.send_message(chat_id, "(пустой ответ)", reply_to_message_id=reply_to)
        return
    first = True
    for i in range(0, len(t), TELEGRAM_CHUNK):
        chunk = t[i : i + TELEGRAM_CHUNK]
        kwargs: dict = {"chat_id": chat_id, "text": chunk}
        if first and reply_to is not None:
            kwargs["reply_to_message_id"] = reply_to
            first = False
        bot.send_message(**kwargs)


def main() -> None:
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        print("Задайте TELEGRAM_BOT_TOKEN в agent/.env", file=sys.stderr)
        sys.exit(1)

    try:
        executor = build_executor(verbose=_verbose_argv)
    except RuntimeError as e:
        _log.error("Агент не собран: %s", e)
        print(e, file=sys.stderr)
        sys.exit(1)

    bot = telebot.TeleBot(token, parse_mode=None)
    _log.info("Telegram-бот запущен, модель %s", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    @bot.message_handler(commands=["start", "help"])
    def cmd_help(message: types.Message) -> None:
        bot.reply_to(
            message,
            "Привет! Пиши вопросы на естественном языке — ответит AI-агент "
            "(погода, поиск, файлы проекта, команды в папке проекта и т.д.).\n\n"
            "/clear — очистить историю этого чата.\n"
            "/help — эта справка.",
        )

    @bot.message_handler(commands=["clear"])
    def cmd_clear(message: types.Message) -> None:
        store = load_telegram_store(TG_MEMORY_FILE)
        cid = message.chat.id
        store.setdefault("chats", {})
        store["chats"][str(cid)] = {"messages": [], "turn_summaries": []}
        save_telegram_store(TG_MEMORY_FILE, store)
        _log.info("chat_id=%s: память очищена", cid)
        bot.reply_to(message, "История диалога в этом чате очищена.")

    @bot.message_handler(content_types=["text"])
    def on_text(message: types.Message) -> None:
        chat_id = message.chat.id
        text = (message.text or "").strip()
        if not text:
            return
        _log.info("chat_id=%s: входящее сообщение len=%s", chat_id, len(text))

        store = load_telegram_store(TG_MEMORY_FILE)
        mem = get_chat_bucket(store, chat_id)
        pairs = pairs_from_memory(mem["messages"])
        history = lc_history_from_pairs(pairs)

        try:
            out = executor.invoke(
                {"input": text, "chat_history": history},
                config={"callbacks": [_trace]},
            )
        except Exception as e:
            _log.exception("chat_id=%s: ошибка invoke", chat_id)
            bot.reply_to(message, f"Ошибка агента: {e}")
            return

        answer = (out.get("output") or "").strip()
        summary = f"Пользователь: {text[:120]}. Ответ: {answer[:200]}"
        append_turn(mem, text, answer, summary)
        save_telegram_store(TG_MEMORY_FILE, store)
        _log.info("chat_id=%s: ответ len=%s", chat_id, len(answer))

        try:
            _send_long(bot, chat_id, answer, reply_to=message.message_id)
        except Exception as e:
            _log.exception("chat_id=%s: не удалось отправить ответ", chat_id)
            bot.reply_to(message, f"Не удалось отправить ответ: {e}")

    _log.info("Polling…")
    bot.infinity_polling(skip_pending=True, interval=0, timeout=60)


if __name__ == "__main__":
    main()
