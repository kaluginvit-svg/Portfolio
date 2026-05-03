# -*- coding: utf-8 -*-
"""SQLite: долгосрочные тезисы по user_id."""
import sqlite3
from pathlib import Path


def connect(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS theses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_theses_user ON theses(user_id)"
    )
    conn.commit()


def add_theses(conn: sqlite3.Connection, user_id: int, items: list[str]) -> int:
    if not items:
        return 0
    n = 0
    for t in items:
        t = (t or "").strip()
        if not t:
            continue
        conn.execute(
            "INSERT INTO theses (user_id, text) VALUES (?, ?)",
            (user_id, t),
        )
        n += 1
    conn.commit()
    return n


def list_theses(conn: sqlite3.Connection, user_id: int) -> list[str]:
    cur = conn.execute(
        "SELECT text FROM theses WHERE user_id = ? ORDER BY id ASC",
        (user_id,),
    )
    return [row["text"] for row in cur.fetchall()]


def clear_theses(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM theses WHERE user_id = ?", (user_id,))
    conn.commit()
