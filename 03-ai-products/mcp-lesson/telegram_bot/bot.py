"""
Telegram-бот: OpenAI Chat Completions + вызовы инструментов product-mcp по HTTP.
"""

from __future__ import annotations

import json
import logging
import textwrap

from openai import AsyncOpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import Config, load_config
from mcp_client import mcp_client_session, mcp_tools_to_openai_functions

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("telegram_bot")

MAX_TOOL_ROUNDS = 8
TELEGRAM_CHUNK = 3900

SYSTEM_PROMPT = textwrap.dedent(
    """\
    Ты вежливый русскоязычный ассистент интернет-магазина с доступом к каталогу товаров через инструменты.

    Правила:
    - Если для ответа нужны факты из каталога, поиск, добавление товара или математика — обязательно вызови соответствующий инструмент.
    - Инструменты: list_products (весь каталог), find_product (поиск по названию), add_product (имя, категория, цена), calculate (арифметическое выражение).
    - Ответы пользователю оформляй структурированно: короткий заголовок, затем списки или абзацы, цены указывай понятно (руб. или число с двумя знаками).
    - Если пользователь формулировку размыта — задай один конкретный уточняющий вопрос вместо догадок.
    - После list_products или find_product не вставляй сырой JSON целиком, если записей много: сделай краткую сводку и при необходимости предложи сузить запрос.
    - Для add_product из фразы вида «добавь яблоки 120 фрукты» извлеки name=яблоки, price=120, category=фрукты (или ближайший смысл категории).
    """
).strip()


def split_for_telegram(text: str, limit: int = TELEGRAM_CHUNK) -> list[str]:
    text = (text or "").strip()
    if not text:
        return ["Пустой ответ."]
    return [text[i : i + limit] for i in range(0, len(text), limit)]


async def run_openai_with_mcp(cfg: Config, user_text: str) -> str:
    client = AsyncOpenAI(
        api_key=cfg.openai_api_key,
        base_url=cfg.openai_base_url,
    )

    async with mcp_client_session(cfg.mcp_base_url) as mcp:
        listed = await mcp.list_tools()
        tools = mcp_tools_to_openai_functions(listed.tools)

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.chat.completions.create(
                model=cfg.openai_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            choice = response.choices[0]
            msg = choice.message

            if not msg.tool_calls:
                return (msg.content or "").strip() or "Модель не вернула текст."

            assistant_payload: dict = {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments or "{}",
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
            messages.append(assistant_payload)

            for tc in msg.tool_calls:
                fn = tc.function
                try:
                    args = json.loads(fn.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                logger.info("MCP tool %s args=%s", fn.name, args)
                tool_text = await mcp.call_tool(fn.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_text,
                    }
                )

        return "Слишком много циклов с инструментами. Сформулируйте запрос короче."


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Привет! Я бот каталога товаров.\n\n"
            "Примеры:\n"
            "• «Покажи все товары»\n"
            "• «Найди чай»\n"
            "• «Добавь товар яблоки, категория фрукты, цена 120»\n"
            "• «Посчитай (199.5 + 20) * 3»\n\n"
            "Сначала должен быть запущен MCP-сервер с `--http` (см. README)."
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg: Config = context.application.bot_data["config"]
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if update.effective_chat:
        await update.effective_chat.send_action(action=ChatAction.TYPING)
    try:
        answer = await run_openai_with_mcp(cfg, text)
    except Exception:
        logger.exception("Ошибка OpenAI/MCP")
        await update.message.reply_text(
            "Не получилось обработать запрос. Проверьте, что MCP-сервер запущен "
            f"на {cfg.mcp_base_url}, ключи OpenAI заданы, и попробуйте снова."
        )
        return

    for chunk in split_for_telegram(answer):
        await update.message.reply_text(chunk)


def main() -> None:
    cfg = load_config()
    app = (
        Application.builder()
        .token(cfg.telegram_api_token)
        .build()
    )
    app.bot_data["config"] = cfg
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    logger.info("Бот запущен, MCP URL: %s, модель: %s", cfg.mcp_base_url, cfg.openai_model)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
