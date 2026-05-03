"""
Расширенный ассистент VPg07: RAG по глобальной knowledge-base и по загруженным пользователем файлам.
"""

from __future__ import annotations

from typing import Any

from Haystack.haystack_agent import (
    AssistantResponse,
    HaystackTelegramAssistant,
    _extract_knowledge_snippets,
    _log,
    _short,
)


class HaystackV2Assistant(HaystackTelegramAssistant):
    """Добавляет поиск по чанкам user_file в том же namespace, что и knowledge-base."""

    def __init__(self, memory_manager: Any = None) -> None:
        super().__init__(memory_manager=memory_manager)
        self._current_user_id: int | None = None

    def run(self, *, user_id: int, message_text: str) -> AssistantResponse:
        self._current_user_id = user_id
        try:
            return super().run(user_id=user_id, message_text=message_text)
        finally:
            self._current_user_id = None

    def _load_knowledge_context(self, message_text: str) -> list[str]:
        uid = self._current_user_id
        merged: list[str] = []
        seen: set[str] = set()

        def add_from_result(result: Any, limit: int) -> None:
            for s in _extract_knowledge_snippets(result, limit=limit):
                if s not in seen:
                    seen.add(s)
                    merged.append(s)

        kb_k = max(1, self.knowledge_top_k - 1)
        try:
            r_kb = self.memory_manager.query_by_text(
                text=message_text,
                top_k=kb_k,
                namespace=self.knowledge_namespace,
                filter={"doc_type": "knowledge"},
                include_metadata=True,
                include_values=False,
            )
            add_from_result(r_kb, kb_k)
        except Exception as exc:
            _log("KNOWLEDGE_ERR", error=repr(exc))

        if uid is not None:
            try:
                r_u = self.memory_manager.query_by_text(
                    text=message_text,
                    top_k=max(2, self.knowledge_top_k),
                    namespace=self.knowledge_namespace,
                    filter={"user_id": uid, "doc_type": "user_file"},
                    include_metadata=True,
                    include_values=False,
                )
                add_from_result(r_u, self.knowledge_top_k)
            except Exception as exc:
                _log("KNOWLEDGE_ERR", user_id=uid, error=repr(exc))

        _log(
            "KNOWLEDGE",
            found=len(merged),
            items=repr([_short(x, 70) for x in merged[:5]]),
        )
        return merged[: self.knowledge_top_k]
