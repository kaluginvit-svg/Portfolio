# Шпаргалка по RAG (актуальные материалы LangChain)

Официальный индекс документации: [https://docs.langchain.com/llms.txt](https://docs.langchain.com/llms.txt)

- Быстрый старт Python: [LangChain Quickstart](https://docs.langchain.com/oss/python/langchain/quickstart)
- RAG / retrieval: [RAG в LangChain (Python)](https://docs.langchain.com/oss/python/langchain/rag)
- Эмбеддинги и OpenAI-совместимые эндпоинты: задаём **`openai_api_base`** (у нас ProxyAPI → `PROXYAPI_BASE_URL`).

В этом проекте рабочая реализация лежит в **`rag_agent.py`** (Pinecone через **`pine.py`**, BYO-векторы, не integrated index).
