"""
Telegram-бот с короткой памятью (history buffer) на aiogram 3.x + OpenAI.

Запуск:
1) Установить зависимости: pip install -r requirements.txt
2) Создать .env на основе .env.example
3) Запустить: python bot_short_memory.py
"""

import asyncio
import logging
import os
from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional, TypedDict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI

# -----------------------------
# Константы и память
# -----------------------------
MAX_HISTORY_MESSAGES = 10  # последние N сообщений (user + assistant) на пользователя


class ChatMessage(TypedDict):
    role: str  # "system" | "user" | "assistant"
    content: str


# Память в RAM: user_id -> кольцевая очередь сообщений
memory: Dict[int, Deque[ChatMessage]] = defaultdict(
    lambda: deque(maxlen=MAX_HISTORY_MESSAGES)
)

router = Router()
openai_client: Optional[AsyncOpenAI] = None


def require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Требуется переменная окружения: {var_name}")
    return value


def pick_api_key() -> str:
    """Берем ключ либо из OPENAI_API_KEY, либо из PROXYAPI_KEY."""
    key = os.getenv("OPENAI_API_KEY") or os.getenv("PROXYAPI_KEY")
    if not key:
        raise RuntimeError("Нужен OPENAI_API_KEY или PROXYAPI_KEY в .env")
    return key


def build_messages_for_openai(user_id: int, user_text: str) -> List[ChatMessage]:
    """
    Формирует payload для Chat Completions:
    - system prompt
    - короткая история пользователя
    - текущее сообщение пользователя
    """
    history = list(memory[user_id])  # уже ограничена MAX_HISTORY_MESSAGES

    system_prompt: ChatMessage = {
        "role": "system",
        "content": "Ты дружелюбный и лаконичный помощник. Отвечай по делу.",
    }

    return [system_prompt, *history, {"role": "user", "content": user_text}]


async def generate_reply(
    client: AsyncOpenAI, model: str, messages: List[ChatMessage]
) -> str:
    """Запрашивает ответ модели OpenAI Chat Completions."""
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=500,
    )
    return (completion.choices[0].message.content or "").strip()


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(
        "Привет! Я бот с короткой памятью.\n"
        f"Я помню последние {MAX_HISTORY_MESSAGES} сообщений в диалоге."
    )


@router.message(F.text)
async def on_text(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    if openai_client is None:
        await message.answer("OpenAI клиент не инициализирован.")
        return

    user_id = message.from_user.id
    user_text = message.text.strip()
    if not user_text:
        await message.answer("Отправь текстовое сообщение.")
        return

    # Формируем запрос к модели из памяти + текущего сообщения.
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    messages_payload = build_messages_for_openai(user_id, user_text)

    try:
        reply_text = await generate_reply(openai_client, model, messages_payload)
    except Exception:
        logging.exception("OpenAI error")
        await message.answer("Не удалось получить ответ от модели. Попробуйте позже.")
        return

    if not reply_text:
        reply_text = "Я не смог сгенерировать ответ. Попробуйте переформулировать вопрос."

    # Обновляем память только после успешной генерации ответа.
    memory[user_id].append({"role": "user", "content": user_text})
    memory[user_id].append({"role": "assistant", "content": reply_text})

    await message.answer(reply_text)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    load_dotenv()

    bot_token = require_env("BOT_TOKEN")
    api_key = pick_api_key()
    base_url = os.getenv("OPENAI_BASE_URL")

    global openai_client
    if base_url:
        openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    else:
        openai_client = AsyncOpenAI(api_key=api_key)

    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    logging.info("Бот запущен. Ожидаю сообщения...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
