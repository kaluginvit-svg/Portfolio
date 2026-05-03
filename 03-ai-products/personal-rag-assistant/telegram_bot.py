"""
Telegram long-polling: текст, документы (Docling + ingestion pipeline), память Pinecone.
"""

from __future__ import annotations

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Tuple

import telebot
from dotenv import load_dotenv

from components.messages import should_store_message
from components.summary import summarize_one_sentence
from components.v2_assistant import AssistantResponse, HaystackV2Assistant
from config import BotConfig, load_config
from logging_setup import setup_logging
from pipelines.ingestion_pipeline import build_user_file_ingestion_pipeline, run_ingestion

from pinecone_manager import PineconeManager

logger = logging.getLogger(__name__)

_ALLOWED_EXT = {
    ".pdf",
    ".doc",
    ".docx",
    ".pptx",
    ".html",
    ".htm",
    ".md",
    ".txt",
    ".csv",
}

# Если имя файла без расширения или клиент исказил суффикс — ориентируемся на MIME Telegram.
_MIME_SUFFIX: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.ms-powerpoint": ".ppt",
    "text/html": ".html",
    "text/markdown": ".md",
    "text/plain": ".txt",
    "text/csv": ".csv",
}

_busy_users: set[int] = set()


def _short(text: str, limit: int = 140) -> str:
    compact = re.sub(r"\s+", " ", (text or "").strip())
    return compact if len(compact) <= limit else (compact[: limit - 1] + "…")


def _caption_limit(text: str, limit: int = 1024) -> str:
    cleaned = (text or "").strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + "…"


def _get_user_fields(user: telebot.types.User) -> Tuple[int, str, str, str]:
    return (
        user.id,
        user.username or "",
        user.first_name or "",
        user.last_name or "",
    )


def _send_assistant_response(
    *,
    bot: telebot.TeleBot,
    message: telebot.types.Message,
    response: AssistantResponse,
) -> None:
    if response.mode == "photo" and response.image_url:
        caption = _caption_limit(response.caption or response.text or "Вот фото собаки.")
        bot.send_photo(
            message.chat.id,
            response.image_url,
            caption=caption,
            reply_to_message_id=message.message_id,
        )
        return

    bot.reply_to(message, response.text)


def _kb_namespace() -> str:
    return os.getenv("PINECONE_KB_NAMESPACE", "knowledge-base").strip() or "knowledge-base"


def _temp_suffix_for_document(doc: telebot.types.Document) -> str:
    """
    Суффикс для временного файла (важно для Docling: .bin для PDF часто даёт сбой).
    """
    name = doc.file_name or ""
    suf = Path(name).suffix.lower()
    if suf in _ALLOWED_EXT:
        return suf
    mime = (doc.mime_type or "").split(";")[0].strip().lower()
    if mime in _MIME_SUFFIX:
        return _MIME_SUFFIX[mime]
    if suf:
        return suf
    return ".bin"


def _document_allowed(doc: telebot.types.Document) -> bool:
    name = doc.file_name or ""
    suf = Path(name).suffix.lower()
    mime = (doc.mime_type or "").split(";")[0].strip().lower()

    if suf in _ALLOWED_EXT:
        return True
    if mime in _MIME_SUFFIX:
        return True
    return False


def run_bot(cfg: BotConfig | None = None) -> None:
    setup_logging()
    load_dotenv()
    cfg = cfg or load_config()

    bot = telebot.TeleBot(cfg.telegram_token)
    memory_manager = PineconeManager()
    assistant = HaystackV2Assistant(memory_manager=memory_manager)
    ingest_pipe = build_user_file_ingestion_pipeline(
        memory_manager,
        namespace=_kb_namespace(),
        chunk_size=cfg.user_doc_chunk_size,
    )

    max_bytes = cfg.max_file_mb * 1024 * 1024

    logger.info("telegram_bot started, max_file_mb=%s", cfg.max_file_mb)

    @bot.message_handler(commands=["start"])
    def handle_start(message: telebot.types.Message) -> None:
        bot.reply_to(
            message,
            (
                "Привет! Я ассистент на Haystack.\n"
                "Помню контекст в Pinecone, умею инструменты (кошки, Wikipedia, погода, собаки).\n"
                "Чтобы загрузить файл: скрепка → «Файл» → выбери PDF/DOCX "
                "(не отправляй документ как сжатое фото — нужен именно файл).\n\n"
                "/help — подсказка\n/clear — очистить память"
            ),
        )

    @bot.message_handler(commands=["help"])
    def handle_help(message: telebot.types.Message) -> None:
        bot.reply_to(
            message,
            (
                "Загрузка: скрепка → Файл → PDF или DOCX.\n"
                "Примеры запросов:\n"
                "- Дай факт о кошках\n"
                "- Что такое RAG?\n"
                "- После загрузки файла спроси по его тексту\n\n"
                "/clear — очистить сохранённый контекст в Pinecone."
            ),
        )

    @bot.message_handler(commands=["clear"])
    def handle_clear(message: telebot.types.Message) -> None:
        user = message.from_user
        if not user:
            return

        try:
            assistant.clear_user_context(user.id)
            logger.info("memory cleared user_id=%s", user.id)
            bot.reply_to(message, "Память очищена. Начинаем диалог с чистого листа.")
        except Exception:
            logger.exception("clear failed")
            bot.reply_to(message, "Не удалось очистить память. Попробуйте позже.")

    @bot.message_handler(content_types=["document"])
    def handle_document(message: telebot.types.Message) -> None:
        user = message.from_user
        doc = message.document
        if not user or not doc:
            return

        uid = user.id
        if uid in _busy_users:
            bot.reply_to(message, "Подожди, предыдущий файл ещё обрабатывается.")
            return

        fname = doc.file_name or "file"
        mime_raw = getattr(doc, "mime_type", None) or ""

        logger.info(
            "document user_id=%s file_name=%r mime=%r size=%s",
            uid,
            fname,
            mime_raw,
            getattr(doc, "file_size", None),
        )

        if not _document_allowed(doc):
            suf = Path(fname).suffix.lower()
            bot.reply_to(
                message,
                (
                    f"Формат «{suf or mime_raw or 'неизвестен'}» не поддерживается. "
                    "Пришли PDF, DOC/DOCX, TXT/MD или используй скрепку → Файл."
                ),
            )
            return

        if doc.file_size and doc.file_size > max_bytes:
            bot.reply_to(
                message,
                f"Файл больше {cfg.max_file_mb} МБ — уменьши размер или подними HAY_V2_MAX_FILE_MB в .env.",
            )
            return

        tmp_suffix = _temp_suffix_for_document(doc)

        _busy_users.add(uid)
        bot.reply_to(
            message,
            "Файл получен. Запускаю анализ и сохранение. Это может занять немного времени…",
        )

        tmp_path: str | None = None
        try:
            file_info = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)
            fd, tmp_path = tempfile.mkstemp(suffix=tmp_suffix)
            os.close(fd)
            Path(tmp_path).write_bytes(downloaded)

            markdown_text, stored = run_ingestion(
                pipeline=ingest_pipe,
                file_path=tmp_path,
                user_id=uid,
                filename=fname,
            )
            summary = summarize_one_sentence(client=memory_manager.openai_client, text=markdown_text)

            bot.reply_to(
                message,
                "Готово. Я изучил этот файл, теперь можем его обсудить.",
            )
            bot.reply_to(message, summary)
            logger.info(
                "ingestion_ok user_id=%s file=%s chunks=%s",
                uid,
                _short(fname),
                stored,
            )
        except Exception:
            logger.exception("ingestion failed")
            bot.reply_to(
                message,
                "Не удалось обработать файл. Проверь формат и размер, либо посмотри логи сервера.",
            )
        finally:
            _busy_users.discard(uid)
            if tmp_path:
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except OSError:
                    pass

    @bot.message_handler(content_types=["text"])
    def handle_text(message: telebot.types.Message) -> None:
        user = message.from_user
        if not user:
            return

        user_id, username, first_name, last_name = _get_user_fields(user)
        user_text = (message.text or "").strip()
        if not user_text or user_text.startswith("/"):
            return

        logger.info(
            "msg user_id=%s text=%s",
            user_id,
            repr(_short(user_text)),
        )

        try:
            response = assistant.run(user_id=user_id, message_text=user_text)
            _send_assistant_response(bot=bot, message=message, response=response)
        except Exception:
            logger.exception("assistant.run")
            bot.reply_to(message, "Не получилось обработать сообщение. Попробуйте ещё раз позже.")
            return

        if not should_store_message(user_text):
            return

        try:
            memory_manager.upsert_document(
                document_id=f"{user_id}_{message.message_id}",
                text=user_text,
                metadata={
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "source": "telegram",
                    "message_type": "user_message",
                },
                namespace=assistant.memory_namespace,
                check_similarity=True,
                similarity_filter={"user_id": user_id},
            )
        except Exception as exc:
            logger.warning("memory upsert: %s", exc)

    bot.infinity_polling(skip_pending=True)


def main() -> None:
    cfg = load_config()
    run_bot(cfg)


if __name__ == "__main__":
    main()
