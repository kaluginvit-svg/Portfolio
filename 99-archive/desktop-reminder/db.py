"""Работа с базой данных напоминаний (SQLite)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional, Dict

# Статусы напоминаний
STATUS_PENDING = "Ожидает"
STATUS_DONE = "Готово"
STATUS_OVERDUE = "Просрочено"
STATUS_CANCELLED = "Отменено"
ALL_STATUSES = (STATUS_PENDING, STATUS_DONE, STATUS_OVERDUE, STATUS_CANCELLED)

# Формат хранения даты/времени
DATETIME_FMT = "%Y-%m-%d %H:%M"


def format_dt(dt: datetime) -> str:
    return dt.strftime(DATETIME_FMT)


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, DATETIME_FMT)


class ReminderDB:
    """Простой слой доступа к SQLite с подготовкой схемы."""

    def __init__(self, db_path: str = "reminders.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                remind_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '{STATUS_PENDING}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def add_reminder(self, title: str, description: str, remind_at: datetime) -> None:
        now = format_dt(datetime.now())
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO reminders (title, description, remind_at, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (title, description, format_dt(remind_at), STATUS_PENDING, now, now),
        )
        self.conn.commit()

    def get_reminders(self, status: Optional[str] = None) -> List[Dict]:
        cur = self.conn.cursor()
        if status and status in ALL_STATUSES:
            cur.execute(
                """
                SELECT * FROM reminders
                WHERE status = ?
                ORDER BY remind_at ASC, id ASC;
                """,
                (status,),
            )
        else:
            cur.execute(
                """
                SELECT * FROM reminders
                ORDER BY remind_at ASC, id ASC;
                """
            )
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def delete_reminder(self, reminder_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM reminders WHERE id = ?;", (reminder_id,))
        self.conn.commit()

    def update_status(self, reminder_id: int, status: str) -> None:
        if status not in ALL_STATUSES:
            raise ValueError("Недопустимый статус")
        now = format_dt(datetime.now())
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE reminders
            SET status = ?, updated_at = ?
            WHERE id = ?;
            """,
            (status, now, reminder_id),
        )
        self.conn.commit()

    def update_remind_at(self, reminder_id: int, remind_at: datetime) -> None:
        now = format_dt(datetime.now())
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE reminders
            SET remind_at = ?, updated_at = ?
            WHERE id = ?;
            """,
            (format_dt(remind_at), now, reminder_id),
        )
        self.conn.commit()

    def due_reminders(self, now: datetime) -> List[Dict]:
        """Возвращает напоминания, время которых наступило, со статусом 'Ожидает'."""
        now_str = format_dt(now)
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT * FROM reminders
            WHERE status = ? AND remind_at <= ?
            ORDER BY remind_at ASC;
            """,
            (STATUS_PENDING, now_str),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.conn.close()


__all__ = [
    "ReminderDB",
    "STATUS_PENDING",
    "STATUS_DONE",
    "STATUS_OVERDUE",
    "STATUS_CANCELLED",
    "ALL_STATUSES",
    "DATETIME_FMT",
    "format_dt",
    "parse_dt",
]

