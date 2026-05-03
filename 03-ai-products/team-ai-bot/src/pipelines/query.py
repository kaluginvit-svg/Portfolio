from __future__ import annotations

from src.config import Settings
from src.pipelines.openai_components import create_text_embedder


def create_query_pipeline(document_store, settings: Settings):
    from haystack import Pipeline
    from haystack_integrations.components.retrievers.pinecone import PineconeEmbeddingRetriever

    pipeline = Pipeline()
    pipeline.add_component("text_embedder", create_text_embedder(settings))
    pipeline.add_component(
        "retriever",
        PineconeEmbeddingRetriever(document_store=document_store, top_k=settings.top_k),
    )
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    return pipeline
