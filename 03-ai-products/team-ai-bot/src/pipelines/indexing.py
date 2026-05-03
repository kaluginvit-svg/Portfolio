from __future__ import annotations

from src.config import Settings
from src.pipelines.openai_components import create_document_embedder


def create_indexing_pipeline(document_store, settings: Settings):
    from haystack import Pipeline
    from haystack.components.writers import DocumentWriter
    from haystack.document_stores.types import DuplicatePolicy

    pipeline = Pipeline()
    pipeline.add_component("embedder", create_document_embedder(settings))
    pipeline.add_component(
        "writer",
        DocumentWriter(document_store=document_store, policy=DuplicatePolicy.OVERWRITE),
    )
    pipeline.connect("embedder.documents", "writer.documents")
    return pipeline
