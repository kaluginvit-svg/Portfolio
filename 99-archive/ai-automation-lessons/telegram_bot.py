"""
Telegram-бот: входящий запрос → выбор действия → PDF (тот же дизайн, что в отчётах).
Запуск из корня проекта: python telegram_bot.py
Требуется BOT_TOKEN в .env
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

from client_report import (
    generate_commercial_proposal,
    generate_kp_pdf,
    generate_report_pdf,
    process_dialog_with_ai,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

MODE_PDF = {
    "analysis": "analysis",
    "software": "software",
    "steps": "steps",
}


def _slug_client(name: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", (name or "").strip(), flags=re.U)
    s = re.sub(r"[\s\-]+", "_", s).strip("_")[:50]
    return s or "client"


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Проанализировать входящий запрос", callback_data="m:analysis")],
            [InlineKeyboardButton("🖥 Дать варианты ПО и смету на внедрение", callback_data="m:software")],
            [InlineKeyboardButton("✅ Рекомендуемые шаги", callback_data="m:steps")],
            [InlineKeyboardButton("📄 Сделать коммерческое", callback_data="m:commercial")],
        ]
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.effective_message.reply_text(
        "📥 **Вставьте файл входящего запроса** (файл `.txt` или отправьте текст сообщением).\n\n"
        "После загрузки появятся кнопки действий.",
        parse_mode="Markdown",
    )


async def _read_document_bytes(update: Update) -> tuple[bytes | None, str | None]:
    doc = update.message.document
    if not doc:
        return None, None
    name = (doc.file_name or "").lower()
    mime = (doc.mime_type or "").lower()
    ok_txt = name.endswith(".txt") or mime.startswith("text/plain") or mime == "text/plain"
    if not ok_txt:
        return None, "Нужен текстовый файл `.txt` (или text/plain)."
    tg_file = await doc.get_file()
    data = await tg_file.download_as_bytearray()
    return bytes(data), None


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    transcript: str | None = None

    if update.message.document:
        raw, err = await _read_document_bytes(update)
        if err:
            await update.message.reply_text(err)
            return
        if raw is None:
            return
        try:
            transcript = raw.decode("utf-8")
        except UnicodeDecodeError:
            transcript = raw.decode("utf-8", errors="replace")
    elif update.message.text:
        transcript = update.message.text.strip()
    else:
        return

    if not transcript:
        await update.message.reply_text("Текст пустой. Пришлите содержимое запроса.")
        return

    context.user_data["transcript"] = transcript
    context.user_data.pop("cached_result", None)

    await update.message.reply_text(
        "✅ Запрос получен. Выберите действие:",
        reply_markup=main_keyboard(),
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q or not q.data:
        return
    await q.answer()

    transcript: str | None = context.user_data.get("transcript")
    if not transcript:
        await q.edit_message_text("Сначала отправьте файл или текст входящего запроса. /start")
        return

    mode = q.data.split(":", 1)[-1]
    chat_id = q.message.chat_id

    async def status(text: str) -> None:
        await context.bot.send_message(chat_id=chat_id, text=text)

    loop = asyncio.get_running_loop()

    try:
        if mode == "commercial":
            await status("🔄 Анализ запроса и подготовка данных для КП…")
            if context.user_data.get("cached_result") is None:
                result = await loop.run_in_executor(None, process_dialog_with_ai, transcript)
                context.user_data["cached_result"] = result
            else:
                result = context.user_data["cached_result"]

            await status("📝 Генерация коммерческого предложения…")
            tr, rd = transcript, result.data
            kp = await loop.run_in_executor(
                None,
                lambda tr=tr, rd=rd: generate_commercial_proposal(tr, rd),
            )

            await status("📄 Сборка PDF…")
            slug = _slug_client(result.data.get("client_name", ""))
            fn = f"kp_{slug}_{_stamp()}.pdf"
            path = await loop.run_in_executor(
                None,
                lambda kp=kp, fn=fn: generate_kp_pdf(kp, filename=fn),
            )

            await status("✅ Документ готов! Отправляю файл…")
            with open(path, "rb") as f:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    filename=fn,
                    caption="✅ Коммерческое предложение готово.",
                )
        else:
            pdf_mode = MODE_PDF.get(mode)
            if not pdf_mode:
                await status("Неизвестное действие.")
                return

            await status("🔄 Обработка диалога с помощью ИИ…")
            if context.user_data.get("cached_result") is None:
                result = await loop.run_in_executor(None, process_dialog_with_ai, transcript)
                context.user_data["cached_result"] = result
            else:
                result = context.user_data["cached_result"]

            await status("📝 Генерация PDF-отчёта…")
            slug = _slug_client(result.data.get("client_name", ""))
            fn = f"report_{slug}_{_stamp()}.pdf"
            rd, pm = result.data, pdf_mode
            path = await loop.run_in_executor(
                None,
                lambda rd=rd, pm=pm, fn=fn: generate_report_pdf(rd, mode=pm, filename=fn),
            )

            await status("✅ Отчёт готов! Отправляю файл…")
            with open(path, "rb") as f:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    filename=fn,
                    caption="✅ Отчёт успешно создан!",
                )

        await context.bot.send_message(
            chat_id=chat_id,
            text="Нужен ещё документ по этому же запросу — нажмите кнопку ниже или пришлите новый файл.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔄 Создать новый отчёт", callback_data="noop:new")]]
            ),
        )
    except Exception as e:
        log.exception("callback error")
        await context.bot.send_message(chat_id=chat_id, text=f"Ошибка: {e}")


async def on_callback_noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if q:
        context.user_data.clear()
        await q.answer("Ок — жду новый запрос.")
        await q.edit_message_text(
            "📥 Пришлите **новый** файл входящего запроса или текст.",
            parse_mode="Markdown",
        )


def main() -> None:
    token = (os.getenv("BOT_TOKEN") or "").strip()
    if not token:
        raise SystemExit("Задайте BOT_TOKEN в .env")

    app = (
        Application.builder()
        .token(token)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(
        MessageHandler((filters.Document.ALL | filters.TEXT) & ~filters.COMMAND, on_message)
    )
    app.add_handler(CallbackQueryHandler(on_callback, pattern=r"^m:"))
    app.add_handler(CallbackQueryHandler(on_callback_noop, pattern=r"^noop:"))

    log.info("Бот запущен (polling)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
