from __future__ import annotations

from src.config import Settings


def create_document_embedder(settings: Settings):
    from haystack.components.embedders import OpenAIDocumentEmbedder
    from haystack.utils import Secret

    return OpenAIDocumentEmbedder(
        api_key=Secret.from_token(settings.openai_api_key),
        api_base_url=settings.openai_base_url,
        model=settings.embedding_model,
        meta_fields_to_embed=["author_name", "created_at"],
    )


def create_text_embedder(settings: Settings):
    from haystack.components.embedders import OpenAITextEmbedder
    from haystack.utils import Secret

    return OpenAITextEmbedder(
        api_key=Secret.from_token(settings.openai_api_key),
        api_base_url=settings.openai_base_url,
        model=settings.embedding_model,
    )


def create_chat_generator(settings: Settings):
    from haystack.components.generators.chat import OpenAIChatGenerator
    from haystack.utils import Secret

    return OpenAIChatGenerator(
        api_key=Secret.from_token(settings.openai_api_key),
        api_base_url=settings.openai_base_url,
        model=settings.openai_model,
        generation_kwargs={"temperature": 0.2},
    )
