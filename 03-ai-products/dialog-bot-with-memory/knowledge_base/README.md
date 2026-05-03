# Knowledge Base

Положи сюда `.md` или `.txt` файлы для индексации в Pinecone.

Пример запуска:

```bash
python ingest_knowledge_base.py
```

Файлы будут разрезаны на чанки и записаны в namespace `knowledge-base`
или в namespace из переменной `PINECONE_KB_NAMESPACE`.
