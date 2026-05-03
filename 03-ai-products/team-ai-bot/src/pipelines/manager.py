from __future__ import annotations

import logging
from dataclasses import dataclass

from src.config import Settings
from src.domain.models import ChatMessageRecord
from src.pipelines.indexing import create_indexing_pipeline
from src.pipelines.query import create_query_pipeline
from src.pipelines.summarization import create_summarization_pipeline
from src.storage.pinecone_store import create_pinecone_document_store

logger = logging.getLogger(__name__)


@dataclass
class PipelineManager:
    settings: Settings

    def __post_init__(self) -> None:
        self.document_store = create_pinecone_document_store(self.settings)
        # Each pipeline owns its own component instances. Haystack components are not reused
        # across pipelines to avoid the "component already used" runtime error.
        self.indexing_pipeline = create_indexing_pipeline(self.document_store, self.settings)
        self.query_pipeline = create_query_pipeline(self.document_store, self.settings)
        self.summarization_pipeline = create_summarization_pipeline(self.settings)

    def index_message(self, record: ChatMessageRecord) -> None:
        from haystack import Document

        document = Document(id=record.document_id, content=record.content, meta=record.meta)
        logger.info("Indexing message %s into Pinecone namespace %s", record.document_id, self.settings.pinecone_namespace)
        self.indexing_pipeline.run({"embedder": {"documents": [document]}})

    def search_messages(
        self,
        query: str,
        *,
        chat_id: int,
        session_id: str | None = None,
        top_k: int | None = None,
    ) -> list[object]:
        conditions: list[dict[str, object]] = [
            {"field": "meta.chat_id", "operator": "==", "value": str(chat_id)}
        ]
        if session_id:
            conditions.append({"field": "meta.session_id", "operator": "==", "value": session_id})
        filters: dict[str, object] = {"operator": "AND", "conditions": conditions}

        result = self.query_pipeline.run(
            {
                "text_embedder": {"text": query},
                "retriever": {"filters": filters, "top_k": top_k or self.settings.top_k},
            }
        )
        return result["retriever"]["documents"]

    def run_chat_prompt(self, messages: list[object], template_variables: dict[str, object]) -> str:
        result = self.summarization_pipeline.run(
            {
                "prompt_builder": {
                    "template": messages,
                    "template_variables": template_variables,
                }
            }
        )
        replies = result["llm"]["replies"]
        if not replies:
            return ""
        return getattr(replies[0], "text", str(replies[0]))
