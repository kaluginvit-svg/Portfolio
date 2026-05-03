from __future__ import annotations

import logging
import os
from typing import Any

from src.config import Settings

logger = logging.getLogger(__name__)


def _extract_dimension(description: Any) -> int | None:
    if isinstance(description, dict):
        value = description.get("dimension")
    else:
        value = getattr(description, "dimension", None)
    return int(value) if value is not None else None


def validate_pinecone_index_dimension(settings: Settings) -> None:
    from pinecone import Pinecone

    pc = Pinecone(api_key=settings.pinecone_api_key)
    index_exists = pc.has_index(settings.pinecone_index_name)
    if not index_exists:
        logger.info(
            "Pinecone index %s does not exist yet; Haystack will create it with dimension %s.",
            settings.pinecone_index_name,
            settings.pinecone_index_dimension,
        )
        return

    description = pc.describe_index(settings.pinecone_index_name)
    actual_dimension = _extract_dimension(description)
    if actual_dimension is None:
        logger.warning("Could not read dimension for Pinecone index %s.", settings.pinecone_index_name)
        return

    if actual_dimension != settings.pinecone_index_dimension:
        raise ValueError(
            "Pinecone index dimension mismatch: "
            f"index={settings.pinecone_index_name!r}, actual={actual_dimension}, "
            f"expected={settings.pinecone_index_dimension}. "
            "For text-embedding-3-large the index must be 3072-dimensional."
        )


def create_pinecone_document_store(settings: Settings):
    from haystack.utils import Secret
    from haystack_integrations.document_stores.pinecone import PineconeDocumentStore

    os.environ["PINECONE_API_KEY"] = settings.pinecone_api_key
    validate_pinecone_index_dimension(settings)

    spec = {
        "serverless": {
            "cloud": settings.pinecone_cloud,
            "region": settings.pinecone_region,
        }
    }
    return PineconeDocumentStore(
        api_key=Secret.from_token(settings.pinecone_api_key),
        index=settings.pinecone_index_name,
        namespace=settings.pinecone_namespace,
        dimension=settings.pinecone_index_dimension,
        spec=spec,
        metric="cosine",
    )
