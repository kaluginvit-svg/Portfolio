"""Персистентное FSM-хранилище в SQLite."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from aiogram.fsm.storage.base import BaseStorage, StorageKey

from app.db.session import aconnect

log = logging.getLogger(__name__)


def _state_to_str(state: Any) -> Optional[str]:
    """aiogram передаёт в storage и str, и объект State — в SQLite нужна строка."""
    if state is None:
        return None
    if isinstance(state, str):
        return state
    inner = getattr(state, "state", None)
    if isinstance(inner, str):
        return inner
    return str(state)


def _key_str(key: StorageKey) -> str:
    """Совместимость с aiogram 3.4 (destiny) и более новыми версиями (destination_id и др.)."""
    parts = [
        str(key.bot_id),
        str(key.chat_id),
        str(key.user_id),
        str(key.thread_id or ""),
    ]
    dest = getattr(key, "destiny", None) or getattr(key, "destination_id", None) or ""
    parts.append(str(dest))
    bc = getattr(key, "business_connection_id", None)
    if bc is not None:
        parts.append(str(bc))
    return "|".join(parts)


class SqliteFSMStorage(BaseStorage):
    def __init__(self, db_path: Path) -> None:
        self._path = db_path

    async def set_state(self, key: StorageKey, state: Any = None) -> None:
        k = _key_str(key)
        state_sql = _state_to_str(state)
        async with aconnect(self._path) as conn:
            cur = await conn.execute("SELECT data FROM fsm_storage WHERE key = ?", (k,))
            row = await cur.fetchone()
            raw = row[0] if row else "{}"
            try:
                data = json.loads(raw or "{}")
            except json.JSONDecodeError:
                data = {}
            await conn.execute(
                """
                INSERT INTO fsm_storage (key, state, data) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET state = excluded.state
                """,
                (k, state_sql, json.dumps(data, ensure_ascii=False)),
            )
            await conn.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        k = _key_str(key)
        async with aconnect(self._path) as conn:
            cur = await conn.execute("SELECT state FROM fsm_storage WHERE key = ?", (k,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        k = _key_str(key)
        async with aconnect(self._path) as conn:
            cur = await conn.execute("SELECT state FROM fsm_storage WHERE key = ?", (k,))
            row = await cur.fetchone()
            state = row[0] if row else None
            await conn.execute(
                """
                INSERT INTO fsm_storage (key, state, data) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET data = excluded.data
                """,
                (k, state, json.dumps(dict(data), ensure_ascii=False)),
            )
            await conn.commit()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        k = _key_str(key)
        async with aconnect(self._path) as conn:
            cur = await conn.execute("SELECT data FROM fsm_storage WHERE key = ?", (k,))
            row = await cur.fetchone()
            if not row or not row[0]:
                return {}
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                log.warning("Некорректный JSON FSM для key=%s", k)
                return {}

    async def close(self) -> None:
        pass
