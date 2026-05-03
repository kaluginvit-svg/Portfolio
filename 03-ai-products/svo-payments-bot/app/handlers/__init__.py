"""Регистрация роутеров (порядок важен: сначала узкие фильтры)."""

from __future__ import annotations

import logging

from aiogram import Dispatcher, Router
from aiogram.types import ErrorEvent

from app.config import Settings
from app.handlers import common, flow_existing, flow_new, fallback, lead, quiz_flow, result, start
from app.handlers.deps import InjectDepsMiddleware
from app.repositories.lead_repository import LeadRepository

log = logging.getLogger(__name__)


def register_handlers(dp: Dispatcher, repo: LeadRepository, settings: Settings) -> None:
    inj = InjectDepsMiddleware(repo, settings)
    dp.message.middleware(inj)
    dp.callback_query.middleware(inj)

    err = Router()

    @err.errors()
    async def _global_errors(event: ErrorEvent) -> bool:
        log.exception("Ошибка в обработчике", exc_info=event.exception)
        return True

    dp.include_router(err)
    dp.include_router(start.router)
    dp.include_router(quiz_flow.router)
    dp.include_router(lead.router)
    dp.include_router(flow_existing.router)
    dp.include_router(flow_new.router)
    dp.include_router(result.router)
    dp.include_router(common.router)
    dp.include_router(fallback.router)
