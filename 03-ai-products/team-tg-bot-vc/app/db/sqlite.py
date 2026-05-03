import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.config import settings

# Путь к базе данных берётся из настроек (переменная окружения DATABASE_PATH)
DB_PATH = Path(settings.database_path)


def _connect() -> sqlite3.Connection:
    # New connection per call keeps it simple for beginners.
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                user TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def add_task(text: str, user: str) -> None:
    created_at = datetime.utcnow().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT INTO tasks (text, user, created_at) VALUES (?, ?, ?)",
            (text, user, created_at),
        )


def list_tasks() -> Iterable[tuple[int, str, str, str]]:
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT id, text, user, created_at FROM tasks ORDER BY id ASC"
        )
        return list(cursor.fetchall())
