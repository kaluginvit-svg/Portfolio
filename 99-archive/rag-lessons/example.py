"""Минимальный ориентир под методичку: эмбеддинги + запрос к векторному хранилищу.

Полный класс агента с @tool и LangGraph — в rag_agent.py (не дублируем логику здесь).
Запуск проверки связи с индексом: python rag_agent.py
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

from pine import PineconeVectorClient

load_dotenv(Path(__file__).resolve().parent / ".env")


def main() -> None:
    base = os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1").rstrip("/")
    key = os.getenv("PROXYAPI_API_KEY")
    if not key:
        raise SystemExit("Нужен PROXYAPI_API_KEY")
    host = os.getenv("PINECONE_INDEX_HOST", "").strip()
    idx = os.getenv("PINECONE_INDEX_NAME", "").strip()
    pc = PineconeVectorClient(index_host=host) if host else PineconeVectorClient(index_name=idx or "nemo")
    dim = getattr(pc.check_index(), "dimension", None)
    model = os.getenv("PROXYAPI_EMBEDDING_MODEL", "text-embedding-3-small")
    kw: dict[str, object] = {"model": model, "openai_api_key": key, "openai_api_base": base}
    if dim is not None and "text-embedding-3" in model:
        kw["dimensions"] = dim
    emb = OpenAIEmbeddings(**kw)
    q = os.getenv("SMOKE_QUERY", "проверка связи с Pinecone")
    vec = list(emb.embed_query(q))
    if dim is not None and len(vec) != dim:
        raise SystemExit(f"dim mismatch: vec={len(vec)} index={dim}")
    hits = pc.search_vectors(vec, top_k=1, include_metadata=True)
    n = len(getattr(hits, "matches", []) or [])
    print("example.py OK — запрос:", repr(q[:80]), "| matches:", n)


if __name__ == "__main__":
    main()
