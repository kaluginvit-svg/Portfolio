"""
Pinecone manager module.

Содержит один класс `PineconeManager` для работы с Pinecone (векторная БД)
и создания эмбеддингов через OpenAI API, подключённый через ProxyAPI
посредством `PROXYAPI_BASE_URL`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from pinecone.exceptions.exceptions import NotFoundException


Vector = List[float]
Metadata = Dict[str, Any]

SIMILARITY_THRESHOLD = 0.5


@dataclass(frozen=True)
class _EnvConfig:
    pinecone_api_key: str
    pinecone_index_name: str
    proxyapi_api_key: str
    proxyapi_base_url: str


class PineconeManager:
    """
    PineconeManager — единая точка доступа к операциям с Pinecone и эмбеддингами.

    Что делает:
    - Загружает переменные окружения из `.env` (через `python-dotenv`).
    - Инициализирует OpenAI-клиент с `base_url` для работы через ProxyAPI:
      `OpenAI(api_key=..., base_url=...)`.
    - Инициализирует Pinecone-клиент и подключается к указанному индексу.

    Обязательные переменные окружения в `.env`:
    - `PINECONE_API_KEY`
    - `PINECONE_INDEX_NAME`
    - `PROXYAPI_API_KEY`
    - `PROXYAPI_BASE_URL`

    Совместимость:
    - Если `PROXYAPI_*` не задан, можно использовать `OPENAI_API_KEY` и `OPENAI_BASE_URL`.
    """

    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"
    DEFAULT_CHUNK_SIZE = 3072

    def __init__(self) -> None:
        load_dotenv()
        self._config = self._load_env_config()

        self.openai_model: str = self.DEFAULT_EMBEDDING_MODEL

        # OpenAI через ProxyAPI (base_url указывает на прокси-ендпоинт)
        self.openai_client = OpenAI(
            api_key=self._config.proxyapi_api_key,
            base_url=self._config.proxyapi_base_url,
        )

        self.pinecone_client = Pinecone(api_key=self._config.pinecone_api_key)
        self.index = self.pinecone_client.Index(self._config.pinecone_index_name)

    @staticmethod
    def _require_env(name: str) -> str:
        value = os.getenv(name)
        if not value or not value.strip():
            raise ValueError(
                f"Отсутствует обязательная переменная окружения `{name}`. "
                f"Добавь её в .env (см. .env.example)."
            )
        return value.strip()

    @classmethod
    def _get_proxyapi_api_key(cls) -> str:
        return os.getenv("PROXYAPI_API_KEY", "").strip() or cls._require_env("OPENAI_API_KEY")

    @classmethod
    def _get_proxyapi_base_url(cls) -> str:
        raw = os.getenv("PROXYAPI_BASE_URL", "").strip() or cls._require_env("OPENAI_BASE_URL")

        # Частая ошибка: поставить общий домен без OpenAI-префикса/пути.
        # Для OpenAI-compatible SDK базовый адрес обычно один из:
        # - https://openai.api.proxyapi.ru/v1
        # - https://api.proxyapi.ru/openai/v1
        if raw.rstrip("/") == "https://api.proxyapi.ru/v1":
            return "https://openai.api.proxyapi.ru/v1"

        return raw

    @classmethod
    def _load_env_config(cls) -> _EnvConfig:
        return _EnvConfig(
            pinecone_api_key=cls._require_env("PINECONE_API_KEY"),
            pinecone_index_name=cls._require_env("PINECONE_INDEX_NAME"),
            proxyapi_api_key=cls._get_proxyapi_api_key(),
            proxyapi_base_url=cls._get_proxyapi_base_url(),
        )

    # ----------------------------
    # Embeddings
    # ----------------------------
    def create_embedding(self, text: str) -> List[float]:
        """
        Создаёт эмбеддинг для текста через OpenAI-compatible API (ProxyAPI).

        Args:
            text: Исходный текст

        Returns:
            Список чисел — вектор эмбеддинга
        """
        if not getattr(self, "openai_client", None):
            raise ValueError(
                "OpenAI/ProxyAPI клиент не инициализирован. "
                "Проверь PROXYAPI_API_KEY и PROXYAPI_BASE_URL "
                "(или OPENAI_API_KEY и OPENAI_BASE_URL)."
            )

        if not text or not str(text).strip():
            raise ValueError("Нельзя создать эмбеддинг для пустого текста.")

        response = self.openai_client.embeddings.create(
            model=self.openai_model,
            input=str(text).strip(),
        )
        return list(response.data[0].embedding)

    @classmethod
    def chunk_text(cls, text: str, *, chunk_size: int | None = None) -> List[str]:
        """
        Разбить текст на чанки фиксированного размера (по символам).

        Args:
            text: исходный текст.
            chunk_size: размер чанка в символах. Если не задан — используется `DEFAULT_CHUNK_SIZE`.

        Returns:
            Список чанков (каждый чанк — непустая строка).
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("`text` должен быть непустой строкой.")
        size = chunk_size or cls.DEFAULT_CHUNK_SIZE
        if size <= 0:
            raise ValueError("`chunk_size` должен быть > 0.")

        t = text.strip()
        return [t[i : i + size] for i in range(0, len(t), size)]

    def create_embeddings_for_chunks(
        self,
        text: str,
        *,
        model: str | None = None,
        chunk_size: int | None = None,
    ) -> List[Vector]:
        """
        Создать эмбеддинги для текста, разбитого на чанки.

        Чанкинг делается по символам. Для каждого чанка возвращается отдельный вектор.
        """
        chunks = self.chunk_text(text, chunk_size=chunk_size)
        used_model = model or self.openai_model
        resp = self.openai_client.embeddings.create(model=used_model, input=chunks)
        return [list(item.embedding) for item in resp.data]

    # ----------------------------
    # Upsert vectors
    # ----------------------------
    def _check_similarity(
        self,
        vector: Sequence[float],
        *,
        namespace: Optional[str] = None,
        threshold: Optional[float] = None,
        similarity_filter: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Внутренняя проверка на дубликаты по cosine similarity.

        Делает `query` в Pinecone с `top_k=1`, сравнивает score с порогом и:
        - возвращает {"id": <existing_id>, "score": <float>}, если найден похожий вектор
        - иначе возвращает None

        Args:
            vector: вектор для проверки (list[float]).
            namespace: namespace (опционально).
            threshold: порог сходства. Если None — используется `SIMILARITY_THRESHOLD`.
            similarity_filter: фильтр Pinecone для ограничения поиска (опционально).
        """
        used_threshold = SIMILARITY_THRESHOLD if threshold is None else float(threshold)
        if used_threshold < 0:
            raise ValueError("`threshold` должен быть >= 0.")

        res = self.index.query(
            vector=list(vector),
            top_k=1,
            namespace=namespace,
            filter=dict(similarity_filter) if similarity_filter else None,
            include_metadata=False,
            include_values=False,
        )

        matches = getattr(res, "matches", None) or []
        if not matches:
            return None

        best = matches[0]
        score = float(getattr(best, "score", 0.0) or 0.0)
        if score >= used_threshold:
            return {"id": getattr(best, "id", None), "score": score}
        return None

    def upsert_vector(
        self,
        *,
        vector_id: str,
        values: Sequence[float],
        metadata: Optional[Mapping[str, Any]] = None,
        namespace: Optional[str] = None,
        check_similarity: bool = True,
        threshold: Optional[float] = None,
        similarity_filter: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """
        Записать один вектор в Pinecone.

        Args:
            vector_id: уникальный id записи.
            values: значения вектора.
            metadata: метаданные (dict).
            namespace: namespace (опционально).
            check_similarity: если True — перед вставкой проверяет похожие векторы.
            threshold: порог cosine similarity (если None — `SIMILARITY_THRESHOLD`).
            similarity_filter: фильтр Pinecone для проверки сходства (опционально).

        Returns:
            Словарь статуса операции:
            {
              "action": "inserted" | "updated" | "skipped",
              "similarity_score": float | None,
              "existing_id": str | None
            }
        """
        if not vector_id or not str(vector_id).strip():
            raise ValueError("`vector_id` должен быть непустой строкой.")

        vec_values = list(values)
        vec_metadata = dict(metadata or {})

        existing = None
        if check_similarity:
            existing = self._check_similarity(
                vec_values,
                namespace=namespace,
                threshold=threshold,
                similarity_filter=similarity_filter,
            )

        if existing and existing.get("id"):
            # Похожий вектор найден — обновляем существующую запись (upsert по existing_id)
            existing_id = str(existing["id"])
            vec = (existing_id, vec_values, vec_metadata)
            self.index.upsert(vectors=[vec], namespace=namespace)
            return {
                "action": "updated",
                "similarity_score": float(existing.get("score", 0.0)),
                "existing_id": existing_id,
            }

        vec = (str(vector_id), vec_values, vec_metadata)
        self.index.upsert(vectors=[vec], namespace=namespace)
        return {"action": "inserted", "similarity_score": None, "existing_id": None}

    def upsert_vectors(
        self,
        vectors: Sequence[Mapping[str, Any]],
        *,
        namespace: Optional[str] = None,
    ) -> Any:
        """
        Записать несколько векторов в Pinecone.

        Формат элементов `vectors`:
        - {"id": "...", "values": [...], "metadata": {...}}

        Args:
            vectors: список векторов в формате словарей.
            namespace: namespace (опционально).
        """
        prepared: List[Tuple[str, List[float], Dict[str, Any]]] = []
        for i, item in enumerate(vectors):
            if "id" not in item or "values" not in item:
                raise ValueError(
                    "Каждый элемент `vectors` должен содержать ключи `id` и `values`. "
                    f"Ошибка в элементе #{i}."
                )
            vid = str(item["id"]).strip()
            if not vid:
                raise ValueError(f"`id` в элементе #{i} должен быть непустой строкой.")
            vals = list(item["values"])
            meta = dict(item.get("metadata") or {})
            prepared.append((vid, vals, meta))

        return self.index.upsert(vectors=prepared, namespace=namespace)

    # ----------------------------
    # Upsert documents (text -> embedding)
    # ----------------------------
    def upsert_document(
        self,
        *,
        document_id: Optional[str] = None,
        doc_id: Optional[str] = None,
        text: str,
        metadata: Optional[Mapping[str, Any]] = None,
        namespace: Optional[str] = None,
        store_text_in_metadata_key: str = "text",
        check_similarity: bool = True,
        threshold: Optional[float] = None,
        similarity_filter: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """
        Записать один документ (текст) в Pinecone.

        Текст автоматически преобразуется в эмбеддинг через `create_embedding`,
        после чего результат записывается в Pinecone как один вектор.

        Исходный `text` сохраняется в `metadata` (по умолчанию в ключе `text`).

        Args:
            document_id: id документа/вектора (основной параметр).
            doc_id: alias для `document_id` (обратная совместимость).
            text: текст документа.
            metadata: метаданные.
            namespace: namespace (опционально).
            store_text_in_metadata_key: ключ, под которым сохранять исходный текст в metadata.
        """
        resolved_id = (document_id or doc_id or "").strip()
        if not resolved_id:
            raise ValueError("`document_id` должен быть непустой строкой.")

        embedding = self.create_embedding(text)
        meta = dict(metadata or {})
        if store_text_in_metadata_key:
            meta[store_text_in_metadata_key] = str(text)

        return self.upsert_vector(
            vector_id=resolved_id,
            values=embedding,
            metadata=meta,
            namespace=namespace,
            check_similarity=check_similarity,
            threshold=threshold,
            similarity_filter=similarity_filter,
        )

    def upsert_documents(
        self,
        documents: Sequence[Mapping[str, Any]],
        *,
        namespace: Optional[str] = None,
        store_text_in_metadata_key: str = "text",
    ) -> Any:
        """
        Записать несколько документов в Pinecone.

        Формат элементов `documents`:
        - {"id": "...", "text": "...", "metadata": {...}}

        Args:
            documents: список документов.
            namespace: namespace (опционально).
            store_text_in_metadata_key: ключ, под которым сохранять исходный текст в metadata.
        """
        prepared: List[Tuple[str, List[float], Dict[str, Any]]] = []
        for i, doc in enumerate(documents):
            if "id" not in doc or "text" not in doc:
                raise ValueError(
                    "Каждый элемент `documents` должен содержать ключи `id` и `text`. "
                    f"Ошибка в элементе #{i}."
                )
            doc_id = str(doc["id"]).strip()
            if not doc_id:
                raise ValueError(f"`id` в элементе #{i} должен быть непустой строкой.")
            text = doc["text"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"`text` в элементе #{i} должен быть непустой строкой.")

            meta_base = dict(doc.get("metadata") or {})
            embedding = self.create_embedding(text)
            if store_text_in_metadata_key:
                meta_base[store_text_in_metadata_key] = text
            prepared.append((doc_id, embedding, meta_base))

        return self.index.upsert(vectors=prepared, namespace=namespace)

    # ----------------------------
    # Search / Query
    # ----------------------------
    def query_by_vector(
        self,
        *,
        vector: Sequence[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Mapping[str, Any]] = None,
        include_metadata: bool = True,
        include_values: bool = False,
    ) -> Any:
        """
        Поиск ближайших соседей по вектору.

        Args:
            vector: вектор запроса.
            top_k: сколько матчей вернуть.
            namespace: namespace (опционально).
            filter: фильтр Pinecone (опционально).
            include_metadata: вернуть metadata.
            include_values: вернуть values.
        """
        if top_k <= 0:
            raise ValueError("`top_k` должен быть > 0.")

        return self.index.query(
            vector=list(vector),
            top_k=top_k,
            namespace=namespace,
            filter=dict(filter) if filter else None,
            include_metadata=include_metadata,
            include_values=include_values,
        )

    def query_by_text(
        self,
        *,
        text: str,
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Mapping[str, Any]] = None,
        include_metadata: bool = True,
        include_values: bool = False,
    ) -> Any:
        """
        Поиск по тексту.

        Текст сначала преобразуется в эмбеддинг, затем выполняется vector search.
        """
        vec = self.create_embedding(text)
        return self.query_by_vector(
            vector=vec,
            top_k=top_k,
            namespace=namespace,
            filter=filter,
            include_metadata=include_metadata,
            include_values=include_values,
        )

    # Backward-compatible aliases
    def search_by_vector(self, **kwargs: Any) -> Any:  # pragma: no cover
        """Alias for `query_by_vector` (backward compatibility)."""
        return self.query_by_vector(**kwargs)

    def search_by_text(self, **kwargs: Any) -> Any:  # pragma: no cover
        """Alias for `query_by_text` (backward compatibility)."""
        return self.query_by_text(**kwargs)

    # ----------------------------
    # Fetch / Get
    # ----------------------------
    def fetch_vectors(
        self,
        ids: Sequence[str],
        *,
        namespace: Optional[str] = None,
    ) -> Any:
        """
        Получить векторы (записи) по списку id.
        """
        if not ids:
            raise ValueError("`ids` не должен быть пустым.")
        cleaned = [str(i).strip() for i in ids if str(i).strip()]
        if not cleaned:
            raise ValueError("`ids` не должен быть пустым (после очистки).")
        return self.index.fetch(ids=cleaned, namespace=namespace)

    # Backward-compatible aliases
    def fetch_by_ids(self, ids: Sequence[str], *, namespace: Optional[str] = None) -> Any:  # pragma: no cover
        """Alias for `fetch_vectors` (backward compatibility)."""
        return self.fetch_vectors(ids, namespace=namespace)

    def fetch_by_id(self, vector_id: str, *, namespace: Optional[str] = None) -> Any:  # pragma: no cover
        """Alias for fetching a single id (backward compatibility)."""
        return self.fetch_vectors([vector_id], namespace=namespace)

    # ----------------------------
    # Delete
    # ----------------------------
    def delete(
        self,
        ids: Sequence[str],
        *,
        namespace: Optional[str] = None,
    ) -> Any:
        """
        Удалить записи по списку id.

        Args:
            ids: список id для удаления.
            namespace: namespace (опционально).
        """
        if not ids:
            raise ValueError("`ids` не должен быть пустым.")
        cleaned = [str(i).strip() for i in ids if str(i).strip()]
        if not cleaned:
            raise ValueError("`ids` не должен быть пустым (после очистки).")
        return self.index.delete(ids=cleaned, namespace=namespace)

    # Backward-compatible aliases
    def delete_by_ids(self, ids: Sequence[str], *, namespace: Optional[str] = None) -> Any:  # pragma: no cover
        """Alias for `delete` (backward compatibility)."""
        return self.delete(ids, namespace=namespace)

    def delete_by_id(self, vector_id: str, *, namespace: Optional[str] = None) -> Any:  # pragma: no cover
        """Alias for deleting a single id (backward compatibility)."""
        return self.delete([vector_id], namespace=namespace)

    def delete_by_filter(
        self,
        filter: Mapping[str, Any],
        *,
        namespace: Optional[str] = None,
    ) -> Any:
        """
        Удалить записи по фильтру Pinecone.
        """
        if not filter:
            raise ValueError("`filter` не должен быть пустым.")
        try:
            return self.index.delete(filter=dict(filter), namespace=namespace)
        except NotFoundException:
            # Для пустого индекса/namespace Pinecone может вернуть 404.
            # Для бота это эквивалентно состоянию "удалять нечего".
            return {"matched": 0, "status": "namespace_not_found"}

    def delete_all(self, *, namespace: Optional[str] = None) -> Any:
        """
        Удалить все записи в индексе (или в namespace, если указан).
        """
        return self.index.delete(delete_all=True, namespace=namespace)

    # ----------------------------
    # Stats
    # ----------------------------
    def describe_index_stats(self) -> Any:
        """
        Получить статистику индекса Pinecone.
        """
        return self.index.describe_index_stats()

    # Backward-compatible alias
    def get_index_stats(self) -> Any:  # pragma: no cover
        """Alias for `describe_index_stats` (backward compatibility)."""
        return self.describe_index_stats()

    # ----------------------------
    # Update metadata
    # ----------------------------
    def update_metadata(
        self,
        *,
        vector_id: str,
        metadata: Mapping[str, Any],
        namespace: Optional[str] = None,
    ) -> Any:
        """
        Обновить metadata у существующей записи.

        В Pinecone это делается через `index.update(..., set_metadata=...)`.
        """
        if not vector_id or not str(vector_id).strip():
            raise ValueError("`vector_id` должен быть непустой строкой.")
        if metadata is None:
            raise ValueError("`metadata` не должен быть None.")
        return self.index.update(
            id=str(vector_id),
            set_metadata=dict(metadata),
            namespace=namespace,
        )


if __name__ == "__main__":
    print("=== Ручной тест PineconeManager ===")

    manager = PineconeManager()
    print("Менеджер успешно создан")

    print("\n=== Статистика индекса ===")
    stats = manager.describe_index_stats()
    print(stats)

    test_user_id = 999999

    print("\n=== Тест 1: первая запись ===")
    result_1 = manager.upsert_document(
        document_id="manual_test_mem_1",
        text="Хочу на Марс",
        metadata={"user_id": test_user_id, "source": "manual_test"},
        check_similarity=True,
        similarity_filter={"user_id": test_user_id},
    )
    print(result_1)

    print("\n=== Тест 2: похожая запись ===")
    result_2 = manager.upsert_document(
        document_id="manual_test_mem_2",
        text="Я полечу на Марс",
        metadata={"user_id": test_user_id, "source": "manual_test"},
        check_similarity=True,
        similarity_filter={"user_id": test_user_id},
    )
    print(result_2)

    print("\n=== Тест 3: новая тема ===")
    result_3 = manager.upsert_document(
        document_id="manual_test_mem_3",
        text="Я люблю пиццу",
        metadata={"user_id": test_user_id, "source": "manual_test"},
        check_similarity=True,
        similarity_filter={"user_id": test_user_id},
    )
    print(result_3)

    print("\n=== Поиск по тексту ===")
    search_result = manager.query_by_text(
        text="Кто хочет на Марс?",
        top_k=3,
        filter={"user_id": test_user_id},
    )
    print(search_result)

    print("\n=== Получение записи по ID ===")
    fetched = manager.fetch_vectors(
        ["manual_test_mem_1", "manual_test_mem_2", "manual_test_mem_3"]
    )
    print(fetched)

