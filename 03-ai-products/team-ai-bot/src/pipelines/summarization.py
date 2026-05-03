from __future__ import annotations

from src.config import Settings
from src.pipelines.openai_components import create_chat_generator


def create_summarization_pipeline(settings: Settings):
    from haystack import Pipeline
    from haystack.components.builders import ChatPromptBuilder

    pipeline = Pipeline()
    pipeline.add_component("prompt_builder", ChatPromptBuilder())
    pipeline.add_component("llm", create_chat_generator(settings))
    pipeline.connect("prompt_builder.prompt", "llm.messages")
    return pipeline
