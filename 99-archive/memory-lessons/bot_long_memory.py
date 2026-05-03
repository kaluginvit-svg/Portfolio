"""
Telegram bot with long memory (documents -> embeddings -> retrieval).

Stack:
- aiogram 3.x
- OpenAI Embeddings + Chat Completions
- ChromaDB with persistent storage in ./memory

ENV:
- BOT_TOKEN
- OPENAI_API_KEY
- OPENAI_MODEL (optional, default: gpt-4o-mini)
- OPENAI_EMBED_MODEL (optional, default: text-embedding-3-small)
"""

import asyncio
import logging
import os
import re
import uuid
from pathlib import Path
from typing import List

import chromadb
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI

# -----------------------------
# Settings
# -----------------------------
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
MEMORY_DIR = Path("./memory")
UPLOADS_DIR = Path("./uploads")
COLLECTION_NAME = "documents_memory"

router = Router()
openai_client: AsyncOpenAI | None = None
collection = None


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable '{name}' is not set.")
    return value


def pick_api_key() -> str:
    """Use OPENAI_API_KEY or PROXYAPI_KEY."""
    key = os.getenv("OPENAI_API_KEY") or os.getenv("PROXYAPI_KEY")
    if not key:
        raise RuntimeError("Environment variable 'OPENAI_API_KEY' or 'PROXYAPI_KEY' is required.")
    return key


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split long text into overlapping chunks for better retrieval quality."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    chunks: List[str] = []
    step = max(1, chunk_size - CHUNK_OVERLAP)
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunks.append(normalized[start:end])
        start += step
    return chunks


def load_document(file_path: str) -> str:
    """
    Load document text from TXT / PDF / DOCX.
    Raises RuntimeError if required parser dependency is missing.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise RuntimeError("For PDF support install package: pypdf") from exc

        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    if suffix == ".docx":
        try:
            from docx import Document
        except Exception as exc:
            raise RuntimeError("For DOCX support install package: python-docx") from exc

        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    raise RuntimeError("Unsupported file format. Please upload PDF, TXT, or DOCX.")


async def embed_chunks(user_id: int, file_name: str, text: str) -> int:
    """
    Convert document text to embeddings and store in ChromaDB.
    Returns number of stored chunks.
    """
    if openai_client is None:
        raise RuntimeError("OpenAI client is not initialized.")
    if collection is None:
        raise RuntimeError("Chroma collection is not initialized.")

    embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    chunks = split_text_into_chunks(text, CHUNK_SIZE)
    if not chunks:
        return 0

    # Embed chunks in one request batch.
    embedding_response = await openai_client.embeddings.create(
        model=embed_model,
        input=chunks,
    )
    vectors = [item.embedding for item in embedding_response.data]

    doc_uid = str(uuid.uuid4())
    ids = [f"{user_id}:{doc_uid}:{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "user_id": str(user_id),
            "file_name": file_name,
            "chunk_index": i,
            "doc_uid": doc_uid,
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        embeddings=vectors,
        documents=chunks,
        metadatas=metadatas,
    )
    return len(chunks)


async def retrieve_context(user_id: int, question: str, top_k: int = 5) -> str:
    """Find most relevant document chunks for user's question."""
    if openai_client is None:
        raise RuntimeError("OpenAI client is not initialized.")
    if collection is None:
        raise RuntimeError("Chroma collection is not initialized.")

    embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    query_embed = await openai_client.embeddings.create(model=embed_model, input=question)
    vector = query_embed.data[0].embedding

    # Search only inside this user's uploaded documents.
    result = collection.query(
        query_embeddings=[vector],
        n_results=top_k,
        where={"user_id": str(user_id)},
    )

    docs = result.get("documents", [])
    if not docs or not docs[0]:
        return ""

    # Join retrieved chunks into context block for the LLM.
    context_parts = docs[0]
    return "\n\n---\n\n".join(context_parts)


async def answer_question(question: str, context: str) -> str:
    """Generate answer using only retrieved document context."""
    if openai_client is None:
        raise RuntimeError("OpenAI client is not initialized.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not context.strip():
        return (
            "Я не нашел релевантных фрагментов в загруженных документах. "
            "Сначала отправь документ или уточни вопрос."
        )

    messages = [
        {
            "role": "system",
            "content": (
                "Ты ассистент по работе с документами. "
                "Отвечай только на основе переданного контекста. "
                "Если в контексте нет ответа, честно скажи, что данных недостаточно."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Контекст документа:\n{context}\n\n"
                f"Вопрос: {question}\n\n"
                "Дай точный и краткий ответ по контексту."
            ),
        },
    ]

    completion = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.1,
    )
    text = (completion.choices[0].message.content or "").strip()
    return text or "Не удалось сформировать ответ."


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(
        "Привет! Я бот с долгой памятью по документам.\n"
        "1) Отправь PDF/TXT/DOCX\n"
        "2) Я сохраню в векторную память\n"
        "3) Задавай вопросы по содержимому"
    )


@router.message(F.document)
async def on_document(message: Message, bot: Bot) -> None:
    if message.from_user is None or message.document is None:
        return

    file_name = message.document.file_name or "document"
    suffix = Path(file_name).suffix.lower()
    if suffix not in {".pdf", ".txt", ".docx"}:
        await message.answer("Поддерживаются только файлы PDF, TXT и DOCX.")
        return

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{message.from_user.id}_{uuid.uuid4().hex}{suffix}"
    local_path = UPLOADS_DIR / unique_name

    # Download file from Telegram to local storage.
    tg_file = await bot.get_file(message.document.file_id)
    await bot.download_file(tg_file.file_path, destination=local_path)

    await message.answer("Файл получен. Извлекаю текст и создаю эмбеддинги...")

    try:
        text = await asyncio.to_thread(load_document, str(local_path))
        chunks_count = await embed_chunks(
            user_id=message.from_user.id,
            file_name=file_name,
            text=text,
        )
    except Exception:
        logging.exception("Document processing failed")
        await message.answer(
            "Не удалось обработать документ. Проверь формат файла и зависимости."
        )
        return

    if chunks_count == 0:
        await message.answer("В документе не найден текст для индексации.")
        return

    await message.answer(
        f"Готово. Документ '{file_name}' сохранен в долгую память.\n"
        f"Проиндексировано фрагментов: {chunks_count}."
    )


@router.message(F.text)
async def on_text_question(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    question = message.text.strip()
    if not question:
        await message.answer("Напиши текстовый вопрос.")
        return

    try:
        context = await retrieve_context(user_id=message.from_user.id, question=question)
        answer = await answer_question(question=question, context=context)
    except Exception:
        logging.exception("Question answering failed")
        await message.answer("Ошибка при поиске по памяти документа. Попробуй позже.")
        return

    await message.answer(answer)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    load_dotenv()

    bot_token = require_env("BOT_TOKEN")
    api_key = pick_api_key()
    base_url = os.getenv("OPENAI_BASE_URL")

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Persistent Chroma storage on disk.
    chroma_client = chromadb.PersistentClient(path=str(MEMORY_DIR))
    global collection
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    global openai_client
    if base_url:
        openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    else:
        openai_client = AsyncOpenAI(api_key=api_key)

    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    logging.info("Long-memory bot started.")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
