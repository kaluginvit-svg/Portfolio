from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_session_id(chat_id: int) -> str:
    return f"{chat_id}:{utc_now().strftime('%Y%m%dT%H%M%SZ')}:{uuid4().hex[:8]}"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    STOPPED = "stopped"


@dataclass(frozen=True)
class ListeningSession:
    session_id: str
    chat_id: int
    status: SessionStatus
    started_at: datetime
    stopped_at: datetime | None = None
    message_count: int = 0


@dataclass(frozen=True)
class ChatMessageRecord:
    chat_id: int
    message_id: int
    user_id: int
    username: str
    author_name: str
    text: str
    created_at: datetime
    session_id: str

    @property
    def document_id(self) -> str:
        return f"{self.chat_id}:{self.message_id}:{self.session_id}"

    @property
    def content(self) -> str:
        timestamp = self.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return f"{timestamp}, {self.author_name}: {self.text}"

    @property
    def meta(self) -> dict[str, Any]:
        return {
            "chat_id": str(self.chat_id),
            "message_id": str(self.message_id),
            "user_id": str(self.user_id),
            "username": self.username,
            "author_name": self.author_name,
            "created_at": self.created_at.astimezone(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "source": "telegram",
        }
