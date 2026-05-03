from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.domain.models import ChatMessageRecord, ListeningSession, SessionStatus


def _dt_to_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def _dt_from_text(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class LocalStateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    stopped_at TEXT,
                    message_count INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_chat_status
                    ON sessions(chat_id, status);

                CREATE TABLE IF NOT EXISTS messages (
                    document_id TEXT PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id, created_at);
                """
            )

    def get_active_session(self, chat_id: int) -> ListeningSession | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM sessions
                WHERE chat_id = ? AND status = ?
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (chat_id, SessionStatus.ACTIVE.value),
            ).fetchone()
        return self._session_from_row(row) if row else None

    def save_session(self, session: ListeningSession) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO sessions (
                    session_id, chat_id, status, started_at, stopped_at, message_count
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    session.chat_id,
                    session.status.value,
                    _dt_to_text(session.started_at),
                    _dt_to_text(session.stopped_at),
                    session.message_count,
                ),
            )

    def stop_session(self, session_id: str, stopped_at: datetime) -> ListeningSession | None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE sessions
                SET status = ?, stopped_at = ?
                WHERE session_id = ?
                """,
                (SessionStatus.STOPPED.value, _dt_to_text(stopped_at), session_id),
            )
            row = connection.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return self._session_from_row(row) if row else None

    def increment_message_count(self, session_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE sessions
                SET message_count = message_count + 1
                WHERE session_id = ?
                """,
                (session_id,),
            )

    def save_message(self, record: ChatMessageRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO messages (
                    document_id, chat_id, message_id, user_id, username,
                    author_name, text, created_at, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.document_id,
                    record.chat_id,
                    record.message_id,
                    record.user_id,
                    record.username,
                    record.author_name,
                    record.text,
                    _dt_to_text(record.created_at),
                    record.session_id,
                ),
            )

    def list_session_messages(self, session_id: str) -> list[ChatMessageRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return [self._message_from_row(row) for row in rows]

    def latest_messages(self, chat_id: int, limit: int = 20) -> list[ChatMessageRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM messages
                WHERE chat_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (chat_id, limit),
            ).fetchall()
        return [self._message_from_row(row) for row in reversed(rows)]

    @staticmethod
    def _session_from_row(row: sqlite3.Row) -> ListeningSession:
        return ListeningSession(
            session_id=row["session_id"],
            chat_id=row["chat_id"],
            status=SessionStatus(row["status"]),
            started_at=_dt_from_text(row["started_at"]) or datetime.now(timezone.utc),
            stopped_at=_dt_from_text(row["stopped_at"]),
            message_count=row["message_count"],
        )

    @staticmethod
    def _message_from_row(row: sqlite3.Row) -> ChatMessageRecord:
        return ChatMessageRecord(
            chat_id=row["chat_id"],
            message_id=row["message_id"],
            user_id=row["user_id"],
            username=row["username"],
            author_name=row["author_name"],
            text=row["text"],
            created_at=_dt_from_text(row["created_at"]) or datetime.now(timezone.utc),
            session_id=row["session_id"],
        )
