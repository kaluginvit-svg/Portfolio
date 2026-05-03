"""
Hybrid Telegram bot: short memory + long memory (RAG).

Features:
- aiogram 3.x
- Short memory in RAM (last N dialog messages per user)
- Long memory in ChromaDB (document chunks + embeddings)
- OpenAI-compatible API (OpenAI key or ProxyAPI key)

ENV:
- BOT_TOKEN
- OPENAI_API_KEY or PROXYAPI_KEY
- OPENAI_BASE_URL (optional, for ProxyAPI/OpenAI-compatible gateways)
- OPENAI_MODEL (optional, default: gpt-4o-mini)
- OPENAI_EMBED_MODEL (optional, default: text-embedding-3-small)
"""

import asyncio
import logging
import os
import re
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Deque, Dict, List, Optional, TypedDict

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
SHORT_HISTORY_LIMIT = 10
MEMORY_DIR = Path("./memory")
UPLOADS_DIR = Path("./uploads")
COLLECTION_NAME = "documents_memory"


class ChatMessage(TypedDict):
    role: str
    content: str


router = Router()
openai_client: Optional[AsyncOpenAI] = None
collection = None

# Short memory: user_id -> recent dialog messages
short_memory: Dict[int, Deque[ChatMessage]] = defaultdict(
    lambda: deque(maxlen=SHORT_HISTORY_LIMIT)
)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable '{name}' is not set.")
    return value


def pick_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("PROXYAPI_KEY")
    if not key:
        raise RuntimeError(
            "Environment variable 'OPENAI_API_KEY' or 'PROXYAPI_KEY' is required."
        )
    return key


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
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
    """Load text from TXT/PDF/DOCX file."""
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

    raise RuntimeError("Unsupported format. Please upload PDF, TXT, or DOCX.")


async def embed_chunks(user_id: int, file_name: str, text: str) -> int:
    """Embed document chunks and store them in Chroma."""
    if openai_client is None or collection is None:
        raise RuntimeError("Service is not initialized.")

    embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    chunks = split_text_into_chunks(text)
    if not chunks:
        return 0

    embed_resp = await openai_client.embeddings.create(model=embed_model, input=chunks)
    vectors = [x.embedding for x in embed_resp.data]

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

    collection.add(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)
    return len(chunks)


async def retrieve_context(user_id: int, question: str, top_k: int = 5) -> str:
    """Retrieve most relevant chunks from long memory for this user."""
    if openai_client is None or collection is None:
        raise RuntimeError("Service is not initialized.")

    embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    q = await openai_client.embeddings.create(model=embed_model, input=question)
    q_vector = q.data[0].embedding

    result = collection.query(
        query_embeddings=[q_vector],
        n_results=top_k,
        where={"user_id": str(user_id)},
    )
    docs = result.get("documents", [])
    if not docs or not docs[0]:
        return ""
    return "\n\n---\n\n".join(docs[0])


def build_hybrid_messages(user_id: int, question: str, context: str) -> List[ChatMessage]:
    """Build final prompt from system + retrieved context + short dialog history."""
    history = list(short_memory[user_id])
    context_text = context.strip() or "Контекст по документам не найден."

    return [
        {
            "role": "system",
            "content": (
                "Ты ассистент по документам. "
                "Отвечай по контексту из базы и учитывай короткую историю диалога. "
                "Если контекст не содержит ответа, так и скажи."
            ),
        },
        {
            "role": "system",
            "content": f"Контекст документа:\n{context_text}",
        },
        *history,
        {"role": "user", "content": question},
    ]


async def answer_question(user_id: int, question: str, context: str) -> str:
    """Generate answer using long context + short dialog memory."""
    if openai_client is None:
        raise RuntimeError("OpenAI client is not initialized.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    messages = build_hybrid_messages(user_id=user_id, question=question, context=context)
    completion = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )
    return (completion.choices[0].message.content or "").strip() or "Не удалось сформировать ответ."


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(
        "Привет! Я гибридный бот с короткой и долгой памятью.\n"
        "1) Отправь PDF/TXT/DOCX\n"
        "2) Я сохраню документ в векторную память\n"
        "3) Задавай вопросы и уточняй их в диалоге"
    )


@router.message(F.document)
async def on_document(message: Message, bot: Bot) -> None:
    if message.from_user is None or message.document is None:
        return

    file_name = message.document.file_name or "document"
    suffix = Path(file_name).suffix.lower()
    if suffix not in {".pdf", ".txt", ".docx"}:
        await message.answer("Поддерживаются только PDF, TXT и DOCX.")
        return

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    local_path = UPLOADS_DIR / f"{message.from_user.id}_{uuid.uuid4().hex}{suffix}"

    tg_file = await bot.get_file(message.document.file_id)
    await bot.download_file(tg_file.file_path, destination=local_path)

    await message.answer("Файл получен. Индексирую документ...")

    try:
        text = await asyncio.to_thread(load_document, str(local_path))
        count = await embed_chunks(
            user_id=message.from_user.id,
            file_name=file_name,
            text=text,
        )
    except Exception:
        logging.exception("Document processing failed")
        await message.answer("Не удалось обработать документ.")
        return

    if count == 0:
        await message.answer("В документе не найден текст для индексации.")
        return

    await message.answer(f"Готово. Проиндексировано фрагментов: {count}.")


@router.message(F.text)
async def on_question(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    user_id = message.from_user.id
    question = message.text.strip()
    if not question:
        await message.answer("Напиши текстовый вопрос.")
        return

    try:
        context = await retrieve_context(user_id=user_id, question=question, top_k=5)
        reply = await answer_question(user_id=user_id, question=question, context=context)
    except Exception:
        logging.exception("Question answering failed")
        await message.answer("Ошибка при обработке запроса. Попробуй позже.")
        return

    # Update short memory after successful answer generation.
    short_memory[user_id].append({"role": "user", "content": question})
    short_memory[user_id].append({"role": "assistant", "content": reply})

    await message.answer(reply)


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

    logging.info("Hybrid-memory bot started.")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
