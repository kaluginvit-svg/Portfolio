# Архитектура проекта VPg07

## Дерево

- [`main.py`](main.py) — точка входа (`python main.py`).
- [`telegram_bot.py`](telegram_bot.py) — telebot: текст, документы, блокировка параллельной загрузки.
- [`config.py`](config.py) — проверка обязательных переменных окружения при старте.
- [`components/v2_assistant.py`](components/v2_assistant.py) — `HaystackV2Assistant`: агент и RAG по `user_file` + глобальной базе.
- [`components/summary.py`](components/summary.py) — одно предложение резюме после загрузки файла.
- [`pipelines/ingestion_pipeline.py`](pipelines/ingestion_pipeline.py) — Haystack `Pipeline`: Docling → Markdown → чанки → Pinecone.

## Данные в Pinecone

- Индекс: `PINECONE_INDEX_NAME`.
- Память диалога: namespace `PINECONE_USER_MEMORY_NAMESPACE` (`user-memory`).
- База знаний и загруженные файлы: namespace `PINECONE_KB_NAMESPACE` (`knowledge-base`).

Эмбеддинги через OpenAI-compatible API (`OPENAI_EMBEDDING_MODEL`; под индекс 3072 — `text-embedding-3-large`).
