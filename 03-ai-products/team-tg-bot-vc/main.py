import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import settings
from app.db.sqlite import init_db
from app.handlers.start import router as start_router
from app.handlers.tasks import router as tasks_router


async def main() -> None:
    # Уровень логирования настраивается через переменную окружения LOG_LEVEL
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    # Make sure the database and table exist before the bot starts.
    init_db()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Register routers (handlers)
    dp.include_router(start_router)
    dp.include_router(tasks_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
