"""Обёртка над Pinecone: BYO-векторы и индекс с integrated embedding (см. доки Pinecone)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence

try:
    from dotenv import load_dotenv
    from pinecone import Pinecone, SearchQuery, SearchRerank
    from pinecone.core.openapi.db_data.models import SearchRecordsResponse
    from pinecone.db_data import DescribeIndexStatsResponse, FetchResponse, QueryResponse
    from pinecone.db_data.dataclasses.upsert_response import UpsertResponse
    from pinecone.db_data.types import SearchRerankTypedDict
except ModuleNotFoundError as e:
    raise SystemExit(
        f"Нет зависимости {e.name!r}. Ты запустил не тот Python (без venv).\n"
        "Из папки проекта выполни:\n"
        "  .\\venv\\Scripts\\python.exe pine.py\n"
        "или активируй venv, затем снова python pine.py.\n"
        "Первый раз: .\\venv\\Scripts\\pip install -r requirements.txt"
    ) from e


class PineconeVectorClient:
    """Клиент Pinecone для двух сценариев из `Indexing overview`.

    1) **Integrated embedding** — индекс с hosted-моделью эмбеддингов: пишешь **текст** (`upsert_records`),
       ищешь **текстом** (`search_records` / здесь `search_text_records`). См. шаги в доке:
       https://docs.pinecone.io/guides/index-data/indexing-overview#integrated-embedding
       Ограничение: для таких индексов не поддерживаются update/import **текстом** (там же в разделе).

    2) **Bring your own vectors** — сам считаешь эмбеддинги (например через OpenAI/ProxyAPI),
       в индекс кладёшь `id` + `values`, поиск — вектором запроса. См.:
       https://docs.pinecone.io/guides/index-data/indexing-overview#bring-your-own-vectors

    Namespace: операции всегда в одном namespace; при multitenancy — отдельный namespace на клиента.
    Для integrated в API дефолтный namespace часто задают как `"__default__"` (см. upsert text в доке).

    Переменные окружения: `PINECONE_API_KEY`, `PINECONE_INDEX_HOST` **или** имя индекса через аргумент `index_name`,
    опционально `PINECONE_NAMESPACE`.

    Входы/выходы — в docstring каждого метода.
    """

    def __init__(
        self,
        api_key: str | None = None,
        index_host: str | None = None,
        *,
        index_name: str | None = None,
        default_namespace: str | None = None,
    ) -> None:
        load_dotenv(Path(__file__).resolve().parent / ".env")
        key = api_key or os.environ.get("PINECONE_API_KEY")
        if not key:
            raise ValueError("Нужен api_key или переменная окружения PINECONE_API_KEY.")
        self._default_namespace = default_namespace if default_namespace is not None else os.environ.get(
            "PINECONE_NAMESPACE"
        )
        self._pc = Pinecone(api_key=key)
        if index_host is not None:
            resolved_host = index_host
        elif index_name is not None:
            resolved_host = self._pc.describe_index(index_name).host
        else:
            resolved_host = os.environ.get("PINECONE_INDEX_HOST") or ""
        if not resolved_host:
            raise ValueError("Нужен index_host, index_name или переменная окружения PINECONE_INDEX_HOST.")
        self._index = self._pc.Index(host=resolved_host)

    def _ns(self, namespace: str | None) -> str | None:
        return self._default_namespace if namespace is None else namespace

    def _ns_embedded(self, namespace: str | None) -> str:
        """Дефолтный namespace для upsert_records / search_records (`__default__` в доке Pinecone)."""
        n = self._ns(namespace)
        return n if n is not None else "__default__"

    def check_index(self, metadata_filter: Mapping[str, Any] | None = None) -> DescribeIndexStatsResponse:
        """Проверка доступа к индексу и статистика (размерность, векторы по namespace и т.д.).

        Вход:
            metadata_filter — опционально: только записи с таким metadata (плоский JSON-фильтр Pinecone).

        Выход:
            DescribeIndexStatsResponse — статистика индекса.
        """
        return self._index.describe_index_stats(filter=dict(metadata_filter) if metadata_filter else None)

    def upsert_text_records(
        self,
        records: Sequence[MutableMapping[str, Any]],
        *,
        namespace: str | None = None,
    ) -> UpsertResponse:
        """Запись текста в индекс **с integrated embedding** (`upsert_records` в SDK).

        В каждой записи: `_id` или `id`, плюс поле с сырьевым текстом — имя поля должно совпадать с
        `field_map` индекса (см. https://docs.pinecone.io/guides/index-data/upsert-data#upsert-text).
        Остальные плоские поля идут в metadata.

        Вход:
            records — список dict-записей под твой `field_map`.
            namespace — если None, используется `PINECONE_NAMESPACE` или литерал `__default__`.

        Выход:
            UpsertResponse — результат upsert со стороны data plane.
        """
        return self._index.upsert_records(self._ns_embedded(namespace), list(records))

    def search_text_records(
        self,
        *,
        query_inputs: Mapping[str, Any],
        top_k: int,
        namespace: str | None = None,
        metadata_filter: Mapping[str, Any] | None = None,
        rerank: SearchRerank | SearchRerankTypedDict | None = None,
        fields: list[str] | None = None,
    ) -> SearchRecordsResponse:
        """Семантический поиск **текстом** в индексе с integrated embedding (`search_records`).

        `query_inputs` — то же, что `inputs` у `SearchQuery`: ключи совпадают с полями индекса / `field_map`
        (например одна строка запроса в поле, которое задано при создании индекса). См. обзор:
        https://docs.pinecone.io/guides/index-data/indexing-overview#integrated-embedding

        Вход:
            query_inputs — словарь входов для эмбеддинга запроса (как в `SearchQuery(inputs=...)`).
            top_k — сколько записей вернуть.
            namespace — см. `upsert_text_records`.
            metadata_filter — фильтр по metadata (плоский объект, операторы `$eq`, `$in`, …).
            rerank — опциональный rerank (объект `SearchRerank` или совместимый dict).
            fields — какие поля записей вернуть; по умолчанию как в SDK (`["*"]`).

        Выход:
            SearchRecordsResponse — ранжированные записи и служебные поля ответа.
        """
        q = SearchQuery(
            inputs=dict(query_inputs),
            top_k=top_k,
            filter=dict(metadata_filter) if metadata_filter else None,
        )
        f = fields if fields is not None else ["*"]
        return self._index.search_records(self._ns_embedded(namespace), query=q, rerank=rerank, fields=f)

    def upsert_vectors(
        self,
        vectors: Sequence[MutableMapping[str, Any]],
        *,
        namespace: str | None = None,
        batch_size: int | None = None,
        show_progress: bool = False,
    ) -> UpsertResponse:
        """Запись готовых dense-векторов (**bring your own vectors**, `upsert` в SDK).

        Вход:
            vectors — записи с ключами `id`, `values` (list[float]); `metadata` — плоский dict, без вложенности
                (см. https://docs.pinecone.io/guides/index-data/indexing-overview#metadata).
            namespace — если None, дефолтный namespace индекса / из `.env`.
            batch_size, show_progress — проброс в SDK.

        Выход:
            UpsertResponse.
        """
        return self._index.upsert(
            vectors=list(vectors),
            namespace=self._ns(namespace),
            batch_size=batch_size,
            show_progress=show_progress,
        )

    def fetch_vectors(self, ids: Sequence[str], *, namespace: str | None = None) -> FetchResponse:
        """Чтение векторов по id (до 1000 id за запрос).

        Вход:
            ids — идентификаторы в выбранном namespace.
            namespace — если None, см. `upsert_vectors`.

        Выход:
            FetchResponse — `vectors`, `namespace`, `usage`.
        """
        return self._index.fetch(ids=list(ids), namespace=self._ns(namespace))

    def search_vectors(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        namespace: str | None = None,
        metadata_filter: Mapping[str, Any] | None = None,
        include_values: bool = False,
        include_metadata: bool = True,
    ) -> QueryResponse:
        """Поиск по **вектору запроса** (BYO-эмбеддинг, операция `query`).

        Вход:
            vector — эмбеддинг запроса, длина = dimension индекса.
            top_k — число ближайших соседей.
            namespace, metadata_filter — как выше; фильтр — плоский JSON Pinecone.
            include_values, include_metadata — что положить в каждый match.

        Выход:
            QueryResponse — `matches`, `namespace`, `usage` и т.д.
        """
        return self._index.query(
            vector=list(vector),
            top_k=top_k,
            namespace=self._ns(namespace),
            filter=dict(metadata_filter) if metadata_filter else None,
            include_values=include_values,
            include_metadata=include_metadata,
        )

    def delete_vectors(
        self,
        *,
        ids: Sequence[str] | None = None,
        delete_all_in_namespace: bool = False,
        metadata_filter: Mapping[str, Any] | None = None,
        namespace: str | None = None,
    ) -> dict[str, Any] | None:
        """Удаление: по id, по metadata-фильтру или все записи в namespace (`delete` в SDK).

        Вход (ровно один режим):
            ids — непустой список id.
            delete_all_in_namespace — очистить namespace целиком.
            metadata_filter — удалить все записи, попадающие под фильтр.
            namespace — для всех режимов; None → дефолт как в `upsert_vectors`.

        Выход:
            dict | None — ответ `delete`.
        """
        ns = self._ns(namespace)
        has_ids = ids is not None and len(ids) > 0
        modes = (has_ids, delete_all_in_namespace, metadata_filter is not None)
        if sum(modes) != 1:
            raise ValueError("Выбери один режим: ids (непустой), delete_all_in_namespace=True или metadata_filter.")
        if has_ids:
            return self._index.delete(ids=list(ids), namespace=ns)
        if delete_all_in_namespace:
            return self._index.delete(delete_all=True, namespace=ns)
        return self._index.delete(filter=dict(metadata_filter), namespace=ns)


def _demo_semantic_search() -> None:
    """Один тестовый RAG-поиск: вопрос → эмбеддинг (ProxyAPI) → Pinecone query."""
    import sys
    from pathlib import Path

    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv(Path(__file__).resolve().parent / ".env")
    question = "какой автомобиль имеет систему дистанционной связи для система беспроводной связи внутри салона с интернетом?"
    proxy_key = os.environ.get("PROXYAPI_API_KEY")
    proxy_base = os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1").rstrip("/")
    embed_model = os.getenv("PROXYAPI_EMBEDDING_MODEL", "text-embedding-3-small")
    # Имя индекса: по умолчанию nemo; пустая строка в .env → берём только PINECONE_INDEX_HOST.
    index_name = os.getenv("PINECONE_INDEX_NAME", "nemo")

    if not proxy_key:
        sys.exit("В .env нужен PROXYAPI_API_KEY для эмбеддинга запроса.")

    pc = PineconeVectorClient(index_name=index_name.strip()) if index_name.strip() else PineconeVectorClient()
    stats = pc.check_index()
    dim = getattr(stats, "dimension", None)

    oai = OpenAI(base_url=proxy_base, api_key=proxy_key)
    if dim is not None and "text-embedding-3" in embed_model:
        emb = oai.embeddings.create(input=question, model=embed_model, dimensions=dim)
    else:
        emb = oai.embeddings.create(input=question, model=embed_model)
    qvec = list(emb.data[0].embedding)

    hits = pc.search_vectors(qvec, top_k=5, include_metadata=True)
    print(f"Запрос: {question!r}\n")
    for m in hits.matches:
        meta = getattr(m, "metadata", None) or {}
        phrase = meta.get("phrase") if isinstance(meta, dict) else None
        if phrase is None and isinstance(meta, dict):
            phrase = meta.get("text")
        tail = (phrase[:120] + "…") if isinstance(phrase, str) and len(phrase) > 120 else phrase
        print(f"  id={m.id!r}  score={m.score:.4f}  {tail!r}")


if __name__ == "__main__":
    # `python pine.py` — тестовый семантический поиск (см. вопрос в _demo_semantic_search).
    # Полный сценарий заливки: `python run_live.py` или `RUN_LIVE_DEMO=1 python pine.py`
    if os.getenv("RUN_LIVE_DEMO", "").lower() in ("1", "true", "yes"):
        import run_live

        run_live.main()
    else:
        _demo_semantic_search()
