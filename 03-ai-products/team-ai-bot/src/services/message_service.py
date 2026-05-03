from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.domain.models import ChatMessageRecord
from src.domain.session_manager import SessionManager
from src.pipelines.manager import PipelineManager
from src.storage.local_state import LocalStateStore
from src.utils.text import clean_text

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(
        self,
        session_manager: SessionManager,
        state_store: LocalStateStore,
        pipeline_manager: PipelineManager,
    ) -> None:
        self.session_manager = session_manager
        self.state_store = state_store
        self.pipeline_manager = pipeline_manager

    def handle_text_message(self, message: Any) -> ChatMessageRecord | None:
        text = clean_text(getattr(message, "text", ""))
        if not text or text.startswith("/"):
            return None

        chat_id = int(message.chat.id)
        active_session = self.session_manager.status(chat_id)
        if active_session is None:
            return None

        record = self._record_from_telegram_message(message, active_session.session_id, text)
        self.state_store.save_message(record)
        self.session_manager.register_message(active_session.session_id)
        self.pipeline_manager.index_message(record)
        logger.info("Stored message %s for session %s", record.message_id, record.session_id)
        return record

    @staticmethod
    def _record_from_telegram_message(message: Any, session_id: str, text: str) -> ChatMessageRecord:
        user = message.from_user
        username = getattr(user, "username", "") or ""
        first_name = getattr(user, "first_name", "") or ""
        last_name = getattr(user, "last_name", "") or ""
        author_name = clean_text(f"{first_name} {last_name}") or username or str(user.id)
        created_at = datetime.fromtimestamp(message.date, tz=timezone.utc)

        return ChatMessageRecord(
            chat_id=int(message.chat.id),
            message_id=int(message.message_id),
            user_id=int(user.id),
            username=username,
            author_name=author_name,
            text=text,
            created_at=created_at,
            session_id=session_id,
        )
