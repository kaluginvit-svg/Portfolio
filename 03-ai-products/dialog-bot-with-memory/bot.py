import os
import re
from typing import Any, Tuple

import telebot
from dotenv import load_dotenv

from Haystack.haystack_agent import AssistantResponse, HaystackTelegramAssistant
from pinecone_manager import PineconeManager


def _short(text: str, limit: int = 140) -> str:
    """Укорачивает текст для логов в одну строку."""
    compact = re.sub(r"\s+", " ", (text or "").strip())
    return compact if len(compact) <= limit else (compact[: limit - 1] + "…")


def _log(event: str, **fields: Any) -> None:
    """Короткий print-лог: одно событие — одна строка."""
    parts = [f"[{event}]"]
    for key, value in fields.items():
        parts.append(f"{key}={value}")
    print(" ".join(parts))


def _get_user_fields(user: telebot.types.User) -> Tuple[int, str, str, str]:
    return (
        user.id,
        user.username or "",
        user.first_name or "",
        user.last_name or "",
    )


def _caption_limit(text: str, limit: int = 1024) -> str:
    cleaned = (text or "").strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"


def should_store_message(text: str) -> bool:
    """
    Сохраняем только осмысленный пользовательский текст.

    Это ключевое требование урока: в Pinecone должен сохраняться только текст сообщений пользователя.
    """
    if not text or not text.strip():
        return False

    normalized = text.strip().lower()
    if normalized.startswith("/"):
        return False

    if len(normalized) < 6:
        return False

    normalized = re.sub(r"\s+", " ", normalized).strip(" \t\n\r.!?,:;\"'()[]{}")

    technical = {"start", "help", "menu", "settings", "clear"}
    if normalized in technical:
        return False

    junk = {
        "ок",
        "ok",
        "okay",
        "понятно",
        "ясно",
        "спасибо",
        "спс",
        "thanks",
        "thx",
        "пж",
        "плиз",
        "pls",
        "привет",
        "здравствуйте",
        "добрый день",
        "доброе утро",
        "добрый вечер",
        "ага",
        "угу",
        "нет",
        "да",
        "хорошо",
        "ладно",
        "отлично",
        "хаха",
        "lol",
    }
    return normalized not in junk


def _send_assistant_response(
    *,
    bot: telebot.TeleBot,
    message: telebot.types.Message,
    response: AssistantResponse,
) -> None:
    if response.mode == "photo" and response.image_url:
        caption = _caption_limit(response.caption or response.text or "Вот фото собаки.")
        bot.send_photo(
            message.chat.id,
            response.image_url,
            caption=caption,
            reply_to_message_id=message.message_id,
        )
        return

    bot.reply_to(message, response.text)


def main() -> None:
    load_dotenv()

    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise ValueError(
            "Не найден TELEGRAM_BOT_TOKEN в .env. "
            "Добавь TELEGRAM_BOT_TOKEN=... (см. .env.example)."
        )

    bot = telebot.TeleBot(token)
    memory_manager = PineconeManager()
    assistant = HaystackTelegramAssistant(memory_manager=memory_manager)

    _log("BOT", status="starting_polling")

    @bot.message_handler(commands=["start"])
    def handle_start(message: telebot.types.Message) -> None:
        bot.reply_to(
            message,
            (
                "Привет! Я персональный ассистент на Haystack.\n"
                "Я помню твой контекст через Pinecone, умею рассказывать факт о кошках, "
                "искать краткие справки в Wikipedia, показывать и анализировать фото собак, "
                "а также сообщать погоду.\n\n"
                "Команды:\n"
                "/help - подсказка\n"
                "/clear - очистить мою память о тебе"
            ),
        )

    @bot.message_handler(commands=["help"])
    def handle_help(message: telebot.types.Message) -> None:
        bot.reply_to(
            message,
            (
                "Попробуй запросы:\n"
                "- Дай факт о кошках\n"
                "- Что такое RAG?\n"
                "- Покажи собаку и расскажи о породе\n"
                "- Какая погода в Москве?\n"
                "- Что ты помнишь из нашего разговора?\n\n"
                "Команда /clear очищает сохраненный контекст в Pinecone."
            ),
        )

    @bot.message_handler(commands=["clear"])
    def handle_clear(message: telebot.types.Message) -> None:
        user = message.from_user
        if not user:
            return

        try:
            assistant.clear_user_context(user.id)
            _log("MEMORY", action="clear_ok", user_id=user.id)
            bot.reply_to(message, "Память очищена. Начинаем диалог с чистого листа.")
        except Exception as exc:
            _log("MEMORY_ERR", where="clear", user_id=user.id, error=repr(exc))
            bot.reply_to(message, "Не удалось очистить память. Посмотри логи и попробуй еще раз.")

    @bot.message_handler(content_types=["text"])
    def handle_text(message: telebot.types.Message) -> None:
        user = message.from_user
        if not user:
            return

        user_id, username, first_name, last_name = _get_user_fields(user)
        user_text = (message.text or "").strip()
        if not user_text or user_text.startswith("/"):
            return

        _log(
            "IN",
            user_id=user_id,
            username=repr(username),
            name=repr(f"{first_name} {last_name}".strip()),
            text=repr(_short(user_text)),
        )

        try:
            response = assistant.run(user_id=user_id, message_text=user_text)
            _log(
                "OUT",
                user_id=user_id,
                mode=response.mode,
                reply=repr(_short(response.caption or response.text)),
                memories=len(response.memories),
                tools=repr(response.source_tools),
                vision_tokens=response.vision_input_tokens_estimate,
            )
            _send_assistant_response(bot=bot, message=message, response=response)
        except Exception as exc:
            _log("BOT_ERR", where="assistant.run", user_id=user_id, error=repr(exc))
            bot.reply_to(message, "Не получилось обработать сообщение. Посмотри логи и попробуй еще раз.")
            return

        if not should_store_message(user_text):
            _log("MEMORY", action="skip_store", reason="should_store_message", user_id=user_id)
            return

        try:
            result = memory_manager.upsert_document(
                document_id=f"{user_id}_{message.message_id}",
                text=user_text,
                metadata={
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "source": "telegram",
                    "message_type": "user_message",
                },
                namespace=assistant.memory_namespace,
                check_similarity=True,
                similarity_filter={"user_id": user_id},
            )
            _log("MEMORY", action="upsert_ok", user_id=user_id, result=repr(result))
        except Exception as exc:
            _log("MEMORY_ERR", where="upsert", user_id=user_id, error=repr(exc))

    bot.infinity_polling()


if __name__ == "__main__":
    main()

