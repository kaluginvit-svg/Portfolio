"""Боевой прогон: upsert демо-записи → stats → fetch → эмбед запроса → vector search (ProxyAPI + Pinecone)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from pine import PineconeVectorClient

load_dotenv(Path(__file__).resolve().parent / ".env")


def _openai_client() -> OpenAI:
    base = os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1").rstrip("/")
    key = os.getenv("PROXYAPI_API_KEY")
    if not key:
        sys.exit("Нет PROXYAPI_API_KEY в .env.")
    return OpenAI(base_url=base, api_key=key)


def _embed(oai: OpenAI, text: str, model: str) -> list[float]:
    r = oai.embeddings.create(input=text, model=model)
    return list(r.data[0].embedding)


def main() -> None:
    phrase = os.getenv("INGEST_PHRASE", "Пицца Пепперони")
    vec_id = os.getenv("INGEST_VECTOR_ID", "demo-pizza-1")
    query = os.getenv("DEMO_QUERY_TEXT", "Что у нас с пиццей и итальянской едой?")
    model = os.getenv("PROXYAPI_EMBEDDING_MODEL", "text-embedding-3-small")

    oai = _openai_client()
    pc = PineconeVectorClient()

    print("=== 1) upsert (идемпотентно, тот же id) ===")
    vector = _embed(oai, phrase, model)
    stats0 = pc.check_index()
    idx_dim = getattr(stats0, "dimension", None)
    if idx_dim is not None and len(vector) != idx_dim:
        sys.exit(f"dimension индекса {idx_dim}, длина эмбеддинга {len(vector)} — поправь PROXYAPI_EMBEDDING_MODEL или индекс.")
    pc.upsert_vectors(
        [{"id": vec_id, "values": vector, "metadata": {"text": phrase, "source": "run_live"}}],
    )
    print(f"upsert ok: id={vec_id!r}, dim={len(vector)}, text={phrase!r}")

    print("\n=== 2) describe_index_stats ===")
    stats = pc.check_index()
    print(f"total_vector_count={getattr(stats, 'total_vector_count', None)} dimension={getattr(stats, 'dimension', None)}")

    print(f"\n=== 3) fetch ids={[vec_id]!r} ===")
    got = pc.fetch_vectors([vec_id])
    print(got)

    print(f"\n=== 4) semantic search query={query!r} top_k=3 ===")
    qvec = _embed(oai, query, model)
    hits = pc.search_vectors(qvec, top_k=3, include_metadata=True)
    for i, m in enumerate(hits.matches, 1):
        meta = getattr(m, "metadata", None)
        print(f"  {i}. id={m.id!r} score={m.score:.6f} metadata={meta}")


if __name__ == "__main__":
    main()
