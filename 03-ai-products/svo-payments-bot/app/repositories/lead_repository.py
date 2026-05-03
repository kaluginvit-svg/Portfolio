"""Доступ к таблице leads (черновики и завершённые заявки)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from app.db.models import LeadRecord
from app.db.session import aconnect

log = logging.getLogger(__name__)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class LeadRepository:
    def __init__(self, db_path: Path) -> None:
        self._path = db_path

    async def delete_incomplete(self, telegram_user_id: int) -> None:
        async with aconnect(self._path) as conn:
            await conn.execute(
                "DELETE FROM leads WHERE telegram_user_id = ? AND completed = 0",
                (telegram_user_id,),
            )
            await conn.commit()

    async def get_incomplete(self, telegram_user_id: int) -> LeadRecord | None:
        async with aconnect(self._path, row_factory=aiosqlite.Row) as conn:
            cur = await conn.execute(
                """
                SELECT * FROM leads
                WHERE telegram_user_id = ? AND completed = 0
                ORDER BY id DESC LIMIT 1
                """,
                (telegram_user_id,),
            )
            row = await cur.fetchone()
            return LeadRecord.from_row(row) if row else None

    async def create_draft(
        self,
        *,
        telegram_user_id: int,
        telegram_username: str | None,
        telegram_first_name: str | None,
        scenario: str,
    ) -> int:
        now = _utc()
        async with aconnect(self._path) as conn:
            cur = await conn.execute(
                """
                INSERT INTO leads (
                    telegram_user_id, telegram_username, telegram_first_name,
                    scenario, completed, pdn_consent, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 0, 0, ?, ?)
                """,
                (telegram_user_id, telegram_username, telegram_first_name, scenario, now, now),
            )
            await conn.commit()
            lid = cur.lastrowid
        log.debug("Создан черновик лида id=%s user=%s", lid, telegram_user_id)
        return int(lid or 0)

    async def update_incomplete(
        self,
        telegram_user_id: int,
        fields: dict[str, Any],
    ) -> None:
        if not fields:
            return
        cols: list[str] = []
        vals: list[Any] = []
        for k, v in fields.items():
            if k == "selected_documents" and v is not None:
                cols.append("selected_documents = ?")
                vals.append(json.dumps(list(v), ensure_ascii=False))
            elif k in (
                "child_monthly_payment_applicable",
                "pdn_consent",
                "completed",
            ):
                cols.append(f"{k} = ?")
                vals.append(1 if v else 0)
            else:
                cols.append(f"{k} = ?")
                vals.append(v)
        cols.append("updated_at = ?")
        vals.append(_utc())
        vals.append(telegram_user_id)
        q = f"UPDATE leads SET {', '.join(cols)} WHERE telegram_user_id = ? AND completed = 0"
        async with aconnect(self._path) as conn:
            await conn.execute(q, vals)
            await conn.commit()

    async def finalize_incomplete(
        self,
        telegram_user_id: int,
        fields: dict[str, Any],
    ) -> None:
        data = {**fields, "completed": True, "completed_at": _utc()}
        await self.update_incomplete(telegram_user_id, data)
