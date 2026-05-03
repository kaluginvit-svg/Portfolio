from __future__ import annotations

from src.domain.models import ListeningSession
from src.pipelines.manager import PipelineManager
from src.storage.local_state import LocalStateStore


class SummaryService:
    def __init__(self, pipeline_manager: PipelineManager, state_store: LocalStateStore) -> None:
        self.pipeline_manager = pipeline_manager
        self.state_store = state_store

    def summarize_session(self, session: ListeningSession) -> str:
        from haystack.dataclasses import ChatMessage

        records = self.state_store.list_session_messages(session.session_id)
        if not records:
            return "В этой сессии нет сохраненных сообщений, резюмировать нечего."

        transcript = "\n".join(record.content for record in records)
        retrieved = self.pipeline_manager.search_messages(
            "ключевые решения спор аргументы задачи action items",
            chat_id=session.chat_id,
            session_id=session.session_id,
            top_k=12,
        )
        retrieved_context = "\n".join(getattr(document, "content", "") or "" for document in retrieved)

        messages = [
            ChatMessage.from_system(
                "Ты AI-фасилитатор рабочей команды. Делай объективное резюме обсуждения, "
                "отделяй факты от предположений и не добавляй данных вне контекста."
            ),
            ChatMessage.from_user(
                "Сессия обсуждения завершена.\n\n"
                "Полная переписка:\n{{ transcript }}\n\n"
                "Дополнительный retrieval-контекст:\n{{ retrieved_context }}\n\n"
                "Верни структурированный итог на русском языке с разделами:\n"
                "1. Краткое резюме\n"
                "2. Позиции участников\n"
                "3. Принятые решения\n"
                "4. Action items: кто / что / срок\n"
                "5. Открытые вопросы\n"
                "6. Нейтральная рекомендация, если был спор"
            ),
        ]
        return self.pipeline_manager.run_chat_prompt(
            messages,
            {"transcript": transcript, "retrieved_context": retrieved_context},
        )
