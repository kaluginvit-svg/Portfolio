# -*- coding: utf-8 -*-
"""
Telegram-бот с краткосрочной памятью (последние N пар сообщений)
и долгосрочной (тезисы в SQLite). LLM: ProxyAPI (OpenAI-совместимый API).
"""
from __future__ import annotations

import logging
import os
import sys
from collections import defaultdict, deque
from pathlib import Path

import telebot
from dotenv import load_dotenv
from openai import OpenAI

import db
from llm_proxy import build_system_prompt, complete_structured

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("nemo-bot")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
PROXYAPI_KEY = os.environ.get("PROXYAPI_KEY", "").strip()
PROXYAPI_BASE_URL = os.environ.get(
    "PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1"
).strip()
MODEL = os.environ.get("MODEL", "gpt-4o-mini").strip()
SQLITE_PATH = Path(os.environ.get("SQLITE_PATH", "data/bot.db"))
MAX_HISTORY_PAIRS = int(os.environ.get("MAX_HISTORY_PAIRS", "20"))

if not TELEGRAM_BOT_TOKEN or not PROXYAPI_KEY:
    log.error("Задайте TELEGRAM_BOT_TOKEN и PROXYAPI_KEY в .env")
    sys.exit(1)

_max_msgs = max(1, MAX_HISTORY_PAIRS * 2)
_user_histories: dict[int, deque] = defaultdict(lambda: deque(maxlen=_max_msgs))

_conn = db.connect(SQLITE_PATH)
db.init_schema(_conn)

client = OpenAI(api_key=PROXYAPI_KEY, base_url=PROXYAPI_BASE_URL)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode=None)


def handle_message(message: telebot.types.Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()
    if not text:
        bot.reply_to(message, "Пришлите текст.")
        return

    log.info("msg user_id=%s len=%s", uid, len(text))

    stored = db.list_theses(_conn, uid)
    system_text = build_system_prompt(stored)

    hist = _user_histories[uid]
    history_messages = [{"role": m["role"], "content": m["content"]} for m in hist]

    try:
        reply = complete_structured(
            client,
            MODEL,
            system_text,
            history_messages,
            text,
        )
    except Exception as e:
        log.exception("LLM error: %s", e)
        bot.reply_to(message, "Ошибка модели. Попробуйте позже или проверьте ключ ProxyAPI.")
        return

    user_visible = (reply.message or "").strip() or "…"
    bot.reply_to(message, user_visible)

    hist.append({"role": "user", "content": text})
    hist.append({"role": "assistant", "content": user_visible})

    n = db.add_theses(_conn, uid, reply.theses)
    log.info("saved theses: %s", n)


@bot.message_handler(commands=["start"])
def cmd_start(message: telebot.types.Message):
    bot.reply_to(
        message,
        "Привет! Я помню последние сообщения в сессии и сохраняю факты в базу.\n"
        "Команды: /mytheses — мои тезисы, /clear — сбросить память.",
    )


@bot.message_handler(commands=["help"])
def cmd_help(message: telebot.types.Message):
    cmd_start(message)


@bot.message_handler(commands=["mytheses"])
def cmd_mytheses(message: telebot.types.Message):
    uid = message.from_user.id if message.from_user else 0
    rows = db.list_theses(_conn, uid)
    if not rows:
        bot.reply_to(message, "В базе пока нет сохранённых тезисов.")
        return
    out = "Сохранённые тезисы:\n\n" + "\n".join(f"• {t}" for t in rows)
    if len(out) > 4000:
        out = out[:3990] + "…"
    bot.reply_to(message, out)


@bot.message_handler(commands=["clear"])
def cmd_clear(message: telebot.types.Message):
    uid = message.from_user.id if message.from_user else 0
    _user_histories.pop(uid, None)
    db.clear_theses(_conn, uid)
    bot.reply_to(message, "Краткая и долгая память для вас очищены.")


@bot.message_handler(content_types=["text"])
def on_text(message: telebot.types.Message):
    handle_message(message)


def main():
    log.info("Starting bot, model=%s, history_pairs=%s", MODEL, MAX_HISTORY_PAIRS)
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
