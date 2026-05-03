"""
Telegram-бот с AI через ProxyAPI. Контекст диалога в памяти.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, Message

from config import AI_MODEL, BOT_TOKEN, MAX_CONTEXT_MESSAGES
from context_manager import add_message, clear_context, get_context
from proxyapi_client import get_ai_response

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

CLEAR_PHRASE = "очистить контекст"

# Команды бота (меню в Telegram)
BOT_COMMANDS = [
    BotCommand(command="start", description="Запуск и приветствие"),
    BotCommand(command="help", description="Справка и список команд"),
    BotCommand(command="stats", description="Статистика использования"),
    BotCommand(command="clear", description="Очистить историю диалога"),
    BotCommand(command="model", description="Показать текущую модель AI"),
    BotCommand(command="context", description="Инфо о контексте (кол-во сообщений)"),
]


async def setup_commands(bot: Bot) -> None:
    """Устанавливает меню команд в Telegram."""
    await bot.set_my_commands(BOT_COMMANDS)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствие по /start."""
    await message.answer(
        "Привет! Я бот с AI (ProxyAPI, gpt-5-mini).\n"
        "Пиши мне сообщения — я буду отвечать с учётом истории диалога.\n\n"
        "Команды: /help — справка, /stats — статистика, /clear — очистить контекст."
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Справка по командам."""
    help_text = (
        "📖 <b>Справка по командам</b>\n\n"
        "/start — приветствие и краткая информация\n"
        "/help — эта справка\n"
        "/stats — статистика использования (ID, контекст, модель)\n"
        "/clear — очистить историю диалога (то же, что фраза «очистить контекст»)\n"
        "/model — показать модель AI\n"
        "/context — сколько сообщений в твоём контексте\n\n"
        "Просто пиши текст — бот ответит с учётом последних сообщений."
    )
    await message.answer(help_text, parse_mode="HTML")


@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Статистика использования: ID, контекст, модель, лимит."""
    user_id = message.from_user.id if message.from_user else 0
    context = get_context(user_id)
    n = len(context)
    stats_text = (
        "📊 <b>Статистика использования</b>\n\n"
        f"👤 Ваш ID: {user_id}\n"
        f"💬 Сообщений в контексте: {n}\n"
        f"🤖 Модель AI: {AI_MODEL}\n"
        f"📈 Максимум сообщений в контексте: {MAX_CONTEXT_MESSAGES}\n\n"
        "Используйте /clear для очистки контекста."
    )
    await message.answer(stats_text, parse_mode="HTML")


@dp.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    """Очистка контекста по команде."""
    user_id = message.from_user.id if message.from_user else 0
    clear_context(user_id)
    await message.answer("✅ Контекст диалога очищен! Можете начать новый разговор.")
    logger.info("User %s очистил контекст (команда /clear)", user_id)


@dp.message(Command("model"))
async def cmd_model(message: Message) -> None:
    """Показать текущую модель AI."""
    await message.answer(f"🤖 Модель: <code>{AI_MODEL}</code> (ProxyAPI)", parse_mode="HTML")


@dp.message(Command("context"))
async def cmd_context(message: Message) -> None:
    """Показать количество сообщений в контексте."""
    user_id = message.from_user.id if message.from_user else 0
    context = get_context(user_id)
    n = len(context)
    await message.answer(
        f"📋 В твоём контексте сейчас <b>{n}</b> сообщений."
        + (" История пуста — начни диалог." if n == 0 else ""),
        parse_mode="HTML",
    )


@dp.message(F.text)
async def handle_text(message: Message) -> None:
    """Обработка текстовых сообщений: контекст + запрос к AI."""
    user_id = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()

    if not text:
        return

    # Очистка контекста по фразе
    if text.lower() == CLEAR_PHRASE:
        clear_context(user_id)
        await message.answer("✅ Контекст очищен. Можешь начать диалог заново.")
        logger.info("User %s очистил контекст", user_id)
        return

    # Собираем сообщения: контекст + новое сообщение пользователя
    context = get_context(user_id)
    messages = context + [{"role": "user", "content": text}]

    try:
        reply = await asyncio.to_thread(get_ai_response, messages)
        add_message(user_id, "user", text)
        add_message(user_id, "assistant", reply)
        await message.answer(reply)
    except ValueError as e:
        logger.warning("Ошибка конфигурации: %s", e)
        await message.answer("❌ Ошибка настройки бота (нет API-ключа). Обратитесь к администратору.")
    except Exception as e:
        logger.exception("Ошибка при запросе к AI: %s", e)
        await message.answer(
            "❌ Не удалось получить ответ. Попробуй позже или напиши «очистить контекст» и начни заново."
        )


async def main() -> None:
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN не задан. Укажите его в .env")
        sys.exit(1)
    await setup_commands(bot)
    logger.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
