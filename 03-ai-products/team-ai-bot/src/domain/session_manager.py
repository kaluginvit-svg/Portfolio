from __future__ import annotations

from dataclasses import dataclass

from src.domain.models import ListeningSession, SessionStatus, new_session_id, utc_now
from src.storage.local_state import LocalStateStore


@dataclass(frozen=True)
class SessionStartResult:
    session: ListeningSession
    already_active: bool


class SessionManager:
    def __init__(self, state_store: LocalStateStore) -> None:
        self.state_store = state_store

    def start(self, chat_id: int) -> SessionStartResult:
        active = self.state_store.get_active_session(chat_id)
        if active is not None:
            return SessionStartResult(session=active, already_active=True)

        session = ListeningSession(
            session_id=new_session_id(chat_id),
            chat_id=chat_id,
            status=SessionStatus.ACTIVE,
            started_at=utc_now(),
        )
        self.state_store.save_session(session)
        return SessionStartResult(session=session, already_active=False)

    def stop(self, chat_id: int) -> ListeningSession | None:
        active = self.state_store.get_active_session(chat_id)
        if active is None:
            return None
        return self.state_store.stop_session(active.session_id, utc_now())

    def status(self, chat_id: int) -> ListeningSession | None:
        return self.state_store.get_active_session(chat_id)

    def register_message(self, session_id: str) -> None:
        self.state_store.increment_message_count(session_id)
