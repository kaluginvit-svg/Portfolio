"""Подключение к SQLite (aiosqlite)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiosqlite


async def _apply_pragmas(conn: aiosqlite.Connection) -> None:
    """WAL + NORMAL — быстрее коммиты; busy_timeout — меньше «database is locked» при нагрузке."""
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA synchronous=NORMAL;")
    await conn.execute("PRAGMA busy_timeout=5000;")


@asynccontextmanager
async def aconnect(
    db_path: Path,
    *,
    row_factory: type | None = None,
) -> AsyncIterator[aiosqlite.Connection]:
    async with aiosqlite.connect(db_path) as conn:
        await _apply_pragmas(conn)
        if row_factory is not None:
            conn.row_factory = row_factory
        yield conn


async def open_connection(db_path: Path) -> aiosqlite.Connection:
    conn = await aiosqlite.connect(db_path)
    await _apply_pragmas(conn)
    conn.row_factory = aiosqlite.Row
    return conn
