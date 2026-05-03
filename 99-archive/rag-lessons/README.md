# Работа с RAG (ZeroCoder, VPg04)

## Что внутри

| Файл | Назначение |
|------|------------|
| `pine.py` | Клиент Pinecone (BYO-векторы). |
| `test.py` | Индексация корпуса (120 строк) → Pinecone. |
| `rag_agent.py` | Класс **RAGAgent**: эмбеддинги ProxyAPI (`openai_api_base`), Pinecone, `@tool` (поиск, **GET catfact.ninja**, ingest URL), эвристика «прочитай страницу» в `run()`, граф LangGraph + **`AGENT_RECURSION_LIMIT`**. |
| `tutor.md` | Ссылки на актуальные страницы LangChain. |
| `example.py` | Минимальный пример: только эмбеддинг + `search_vectors` (без агента). |
| `telegram_bot.py` | Бот: меню команд, `/profile`, `/summary`, `/search`, `/add_text`, URL→эмбеддинги, агент, локальный профиль в `data/user_profiles.json`. |
| `user_store.py` | Локальный профиль (даты, счётчик, заметка из `/remember`). |
| `bot.py` | Упрощённый бот без LangChain (только OpenAI + Pinecone). |

## Установка

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

Скопируй `.env.example` в `.env` и заполни ключи.

## Проверка Pinecone без Telegram

```powershell
.\venv\Scripts\python.exe rag_agent.py
```

Должно напечатать `OK:` и статистику индекса.

## Индексация корпуса

```powershell
.\venv\Scripts\python.exe test.py
```

## Telegram (ДЗ)

```powershell
.\venv\Scripts\python.exe telegram_bot.py
```

- Текст сообщения → агент (retrieve / при необходимости коты или ingest URL).
- **`/add_url https://…`** — парсинг HTML, чанки, эмбеддинги в Pinecone (без цикла агента).
- **`/cat`** — один GET к catfact.ninja.
- **`/запомни …`** / **`Запомни:`** — вектор в Pinecone.

### Защита от зацикливания

1. **`AGENT_RECURSION_LIMIT`** — максимум шагов графа LangGraph (по умолчанию 12). Каждый вызов модели и инструментов считается в лимите.
2. Инструменты **не вызывают LLM** — только Pinecone/HTTP.
3. Внутри одного запуска агента **`ingest_url`** ограничен (не больше 3 раз); команда **`/add_url`** идёт напрямую в `index_url()` без этого лимита.

## Сдача ДЗ

См. требования в уроке: репозиторий / скриншоты / архив.
