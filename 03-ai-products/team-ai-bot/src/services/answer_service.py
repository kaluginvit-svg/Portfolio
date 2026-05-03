from __future__ import annotations

import logging

from src.pipelines.manager import PipelineManager
from src.storage.local_state import LocalStateStore
from src.utils.text import format_documents_for_prompt

logger = logging.getLogger(__name__)


class AnswerService:
    def __init__(self, pipeline_manager: PipelineManager, state_store: LocalStateStore) -> None:
        self.pipeline_manager = pipeline_manager
        self.state_store = state_store

    def answer(self, *, chat_id: int, question: str, session_id: str | None = None) -> str:
        from haystack.dataclasses import ChatMessage

        documents = self.pipeline_manager.search_messages(
            question,
            chat_id=chat_id,
            session_id=session_id,
        )
        context = format_documents_for_prompt(documents)
        if not context:
            latest = self.state_store.latest_messages(chat_id, limit=10)
            context = "\n".join(record.content for record in latest)

        if not context:
            return "Пока нет сохраненного контекста. Запустите /start_listening и отправьте несколько сообщений."

        messages = [
            ChatMessage.from_system(
                "Ты нейтральный AI-помощник команды. Отвечай только по предоставленному "
                "контексту, не выдумывай факты, называй участников и аргументы, если они есть."
            ),
            ChatMessage.from_user(
                "Вопрос пользователя: {{ question }}\n\n"
                "Контекст обсуждения:\n{{ context }}\n\n"
                "Дай короткий, полезный ответ: что уже обсуждали, какие позиции есть, "
                "и какой следующий шаг выглядит разумным."
            ),
        ]
        return self.pipeline_manager.run_chat_prompt(
            messages,
            {"question": question, "context": context},
        )
