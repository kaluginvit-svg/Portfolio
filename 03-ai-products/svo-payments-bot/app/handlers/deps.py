"""Зависимости для middleware (репозиторий, настройки)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import Settings
from app.repositories.lead_repository import LeadRepository


class InjectDepsMiddleware(BaseMiddleware):
    def __init__(self, repo: LeadRepository, settings: Settings) -> None:
        self._repo = repo
        self._settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["repo"] = self._repo
        data["settings"] = self._settings
        return await handler(event, data)
