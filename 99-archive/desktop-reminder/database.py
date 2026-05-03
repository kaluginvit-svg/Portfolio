"""Работа с базой данных напоминаний (SQLite3)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
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


class ReminderDatabase:
    """Слой доступа к базе данных напоминаний."""

    def __init__(self, db_path: str = "reminders.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.initdatabase()

    def initdatabase(self) -> None:
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
                created_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    # CRUD
    def add_reminder(self, title: str, description: str, remind_at: datetime) -> None:
        now = format_dt(datetime.now())
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO reminders (title, description, remind_at, status, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (title, description, format_dt(remind_at), STATUS_PENDING, now),
        )
        self.conn.commit()

    def get_all_reminders(self, status: Optional[str] = None) -> List[Dict]:
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
        return [dict(row) for row in cur.fetchall()]

    def get_due_reminders(self, now: Optional[datetime] = None) -> List[Dict]:
        now = now or datetime.now()
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT * FROM reminders
            WHERE status = ? AND remind_at <= ?
            ORDER BY remind_at ASC;
            """,
            (STATUS_PENDING, format_dt(now)),
        )
        return [dict(row) for row in cur.fetchall()]

    def sort_by_due_time(self, reminders: List[Dict]) -> List[Dict]:
        return sorted(reminders, key=lambda r: parse_dt(r["remind_at"]))

    def update_status(self, reminder_id: int, status: str) -> None:
        if status not in ALL_STATUSES:
            raise ValueError("Недопустимый статус")
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE reminders
            SET status = ?
            WHERE id = ?;
            """,
            (status, reminder_id),
        )
        self.conn.commit()

    def delete_reminder(self, reminder_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM reminders WHERE id = ?;", (reminder_id,))
        self.conn.commit()

    def mark_overdue(self, now: Optional[datetime] = None) -> None:
        """Переводит в 'Просрочено' напоминания старше минуты от текущего времени."""
        now = now or datetime.now()
        older_than = now - timedelta(minutes=1)
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE reminders
            SET status = ?
            WHERE status = ? AND remind_at <= ?;
            """,
            (STATUS_OVERDUE, STATUS_PENDING, format_dt(older_than)),
        )
        self.conn.commit()

    def get_reminder_by_id(self, reminder_id: int) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM reminders WHERE id = ?;", (reminder_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_reminders_count(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reminders;")
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        self.conn.close()


__all__ = [
    "ReminderDatabase",
    "STATUS_PENDING",
    "STATUS_DONE",
    "STATUS_OVERDUE",
    "STATUS_CANCELLED",
    "ALL_STATUSES",
    "DATETIME_FMT",
    "format_dt",
    "parse_dt",
]

