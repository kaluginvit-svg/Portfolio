import asyncio
import logging
import os
import random
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


logger = logging.getLogger(__name__)

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d - %(message)s"
LOG_FILE = os.path.join(os.getenv("LOG_DIR", "logs"), "bot.log")


def setup_logging() -> None:
    """Логи в файл (ротация), stdout для docker logs, и Logtail при наличии токена."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    LOGTAIL_SOURCE_TOKEN = os.getenv("LOGTAIL_SOURCE_TOKEN")
    if LOGTAIL_SOURCE_TOKEN:
        from logtail import LogtailHandler

        handler = LogtailHandler(source_token=LOGTAIL_SOURCE_TOKEN)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        root.addHandler(handler)
        root.info("🚀 LOGTAIL HANDLER ADDED + TEST")
    else:
        root.warning("LOGTAIL_SOURCE_TOKEN is not set")


def get_bot_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Не задан токен бота. Установите переменную окружения BOT_TOKEN "
            "или добавьте её в файл .env (BOT_TOKEN=...)"
        )
    return token


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user_name = message.from_user.full_name if message.from_user else "друг"
    text = (
        f"Привет, {user_name}!\n"
        "Я простой бот-болталка.\n"
        "Напиши мне что-нибудь, и я постараюсь поддержать разговор 🙂"
    )
    await message.answer(text)


@dp.message(F.text)
async def chat(message: Message) -> None:
    text = (message.text or "").strip().lower()

    if any(word in text for word in ("привет", "здравствуй", "здорово", "hi", "hello")):
        replies = [
            "Привет! Как дела?",
            "Рад тебя видеть! Чем занимаешься?",
            "Хей! Что нового?",
        ]
    elif any(word in text for word in ("как дела", "как ты", "как жизнь")):
        replies = [
            "У меня всё отлично, я живу в облаке 😄 А у тебя как?",
            "Работаю 24/7 без выходных. Но не жалуюсь! А ты как?",
        ]
    elif "время" in text:
        replies = [
            "Время — самый ценный ресурс. Как ты его используешь сегодня?",
            "Самое лучшее время начать — прямо сейчас!",
        ]
    elif "алготрейдинг" in text or "трейдинг" in text:
        replies = [
            "Алготрейдинг — это круто! Ты уже пишешь свои стратегии?",
            "Главное в трейдинге — риск-менеджмент. А в остальном поможет код 🙂",
        ]
    else:
        replies = [
            "Интересно… Расскажи подробнее!",
            "Звучит любопытно. А что ты об этом думаешь?",
            "Понимаю. А как бы ты хотел, чтобы было?",
            "Можем поговорить про что угодно: технологии, трейдинг, фильмы…",
        ]

    await message.answer(random.choice(replies))


async def main() -> None:
    setup_logging()

    logger.info("LOGTAIL_TEST: бот стартовал и логгер работает")

    token = get_bot_token()
    bot = Bot(token=token)

    logger.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
