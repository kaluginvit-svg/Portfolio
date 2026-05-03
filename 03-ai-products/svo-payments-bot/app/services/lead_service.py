"""Операции над лидом после согласия (тонкая обёртка над репозиторием)."""

from __future__ import annotations

from typing import Any

from app.repositories.lead_repository import LeadRepository


async def save_completed_lead(
    repo: LeadRepository,
    telegram_user_id: int,
    fields: dict[str, Any],
) -> None:
    await repo.finalize_incomplete(telegram_user_id, fields)
