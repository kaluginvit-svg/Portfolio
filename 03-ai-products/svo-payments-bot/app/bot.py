"""Запуск Telegram-бота (long polling)."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import get_settings
from app.db.base import init_db
from app.db.fsm_storage import SqliteFSMStorage
from app.handlers import register_handlers
from app.logging import setup_logging
from app.repositories.lead_repository import LeadRepository

log = logging.getLogger(__name__)


async def _run() -> None:
    settings = get_settings()
    if not settings.bot_token:
        print(
            "Укажите BOT_TOKEN в .env (см. .env.example).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    setup_logging(settings.log_level)
    await init_db(settings.database_path)

    repo = LeadRepository(settings.database_path)
    storage = SqliteFSMStorage(settings.database_path)
    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)
    register_handlers(dp, repo, settings)

    if settings.admin_chat_id is None:
        log.warning("ADMIN_CHAT_ID не задан — уведомления о заявках отключены")
    if settings.lead_webhook_url:
        log.info("LEAD_WEBHOOK_URL задан — завершённые заявки дублируются POST JSON")

    log.info("Бот запущен")
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
