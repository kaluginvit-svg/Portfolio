"""
Точка входа Telegram-бота: диспетчер, обработчики, OpenAI и Sora (видео).
Python 3.10+, aiogram 3.x, async/await.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import sys
from decimal import Decimal
from pathlib import Path

import httpx
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from openai import APIError, APIStatusError, AsyncOpenAI
from openai.types.completion_usage import CompletionUsage
from openai.types.images_response import ImagesResponse

from cbr import get_usd_rub_rate_with_date
from config import (
    BOT_TOKEN,
    GPT_IMAGE_15_LOW_USD,
    IMAGE_MODEL,
    IMAGE_QUALITY,
    IMAGE_SIZE,
    MEMORY_MAX_MESSAGES,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    PromptsConfig,
    VIDEO_MODEL,
    load_prompts_file,
)
from image_session import ImagePromptSession
from logging_config import setup_logging
from memory import ChatMemoryStore
from pricing import (
    format_chat_cost_block,
    format_chat_cost_block_no_rate,
    format_image_cost_block,
    format_image_cost_block_no_rate,
    format_video_cost_block,
    format_video_cost_block_no_rate,
    image_success_caption,
    video_success_caption,
)
from video_api import videos_create_json
from video_session import VideoPromptSession

setup_logging(Path(__file__).resolve().parent)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Инициализация (конфиг, память, OpenAI)
# ---------------------------------------------------------------------------

PROMPTS: PromptsConfig = load_prompts_file()
MEMORY = ChatMemoryStore(PROMPTS.default_prompt, MEMORY_MAX_MESSAGES)
VIDEO_SESSION = VideoPromptSession()
IMAGE_SESSION = ImagePromptSession()
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

router = Router()

MSG_INSUFFICIENT_FUNDS = "Недостаточно средств"


def _api_error_text_lower(e: APIStatusError) -> str:
    chunks: list[str] = []
    body = e.body
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and err.get("message"):
            chunks.append(str(err["message"]))
        det = body.get("detail")
        if isinstance(det, str):
            chunks.append(det)
    if getattr(e, "message", None):
        chunks.append(str(e.message))
    return " ".join(chunks).lower()


def is_insufficient_funds_error(e: APIStatusError) -> bool:
    """ProxyAPI: 402 или текст про баланс в теле ответа."""
    if e.status_code == 402:
        return True
    t = _api_error_text_lower(e)
    if "insufficient" in t and "balance" in t:
        return True
    if "payment required" in t:
        return True
    return False


async def notify_insufficient_funds(message: Message, status_msg: Message | None = None) -> None:
    """Сообщение всегда дублируется через answer — чтобы было видно в чате."""
    if status_msg:
        try:
            await status_msg.edit_text(f"❌ {MSG_INSUFFICIENT_FUNDS}")
        except Exception:
            pass
    await message.answer(MSG_INSUFFICIENT_FUNDS)


def _video_job_failure_text(api_message: str) -> str:
    """Текст в чат при status=failed (часто приходит по-английски от API)."""
    t = api_message.strip().lower()
    if "moderation" in t:
        return (
            "Запрос отклонён модерацией: описание или референсы не прошли проверку. "
            "Попробуйте другой промпт."
        )
    if "content policy" in t or "safety system" in t:
        return (
            "Генерация не выполнена из‑за политики контента. Измените промпт и попробуйте снова."
        )
    return f"Видео не готово: {api_message}"


def _mode_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for key, entry in PROMPTS.prompts.items():
        row.append(InlineKeyboardButton(text=entry.name, callback_data=f"mode:{key}"))
        if len(row) >= 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _image_bytes_from_response(resp: ImagesResponse) -> bytes:
    """
    ProxyAPI не всегда поддерживает response_format; ответ может быть с url или b64_json.
    """
    if not resp.data:
        raise ValueError("Пустой data в ответе images.generate")
    item = resp.data[0]
    if item.b64_json:
        return base64.standard_b64decode(item.b64_json)
    if item.url:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            r = await client.get(item.url)
            r.raise_for_status()
            return r.content
    raise ValueError("В ответе нет ни b64_json, ни url")


async def _usd_rub_safe() -> tuple[Decimal | None, str | None]:
    """Курс ₽/$ и дата из XML ЦБ (последняя доступная выгрузка)."""
    try:
        return await get_usd_rub_rate_with_date()
    except Exception as e:
        logger.warning("Не удалось получить курс ЦБ РФ: %s", e)
        return None, None


async def _reply_openai(chat_id: int, user_text: str) -> tuple[str, CompletionUsage | None]:
    """Возвращает (текст ответа, usage или None)."""
    mode_key = await MEMORY.get_mode(chat_id)
    system = PROMPTS.get_system_prompt(mode_key)
    history = await MEMORY.get_messages_for_api(chat_id)

    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    logger.info(
        "chat request chat_id=%s mode=%s messages_in_ctx=%s",
        chat_id,
        mode_key,
        len(messages),
    )

    try:
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
    except APIStatusError as e:
        if is_insufficient_funds_error(e):
            logger.warning("chat insufficient funds chat_id=%s status=%s", chat_id, e.status_code)
            raise RuntimeError(MSG_INSUFFICIENT_FUNDS) from e
        logger.exception("OpenAI chat API status error chat_id=%s", chat_id)
        raise RuntimeError(f"Ошибка API: {e.message}") from e
    except APIError as e:
        logger.exception("OpenAI chat API error chat_id=%s", chat_id)
        raise RuntimeError(f"Ошибка API: {e}") from e

    choice = response.choices[0].message
    content = choice.content
    if not content:
        return "(Пустой ответ модели)", response.usage
    return content, response.usage


async def run_video_generation(message: Message, prompt: str) -> None:
    """Отдельная ветка: Sora-2 через Videos API (асинхронный рендер + скачивание)."""
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    logger.info(
        "video branch start chat_id=%s user_id=%s prompt_len=%s model=%s",
        chat_id,
        user_id,
        len(prompt),
        VIDEO_MODEL,
    )

    status_msg = await message.answer(
        "Генерация видео (Sora)… Это может занять несколько минут."
    )

    # Как в официальной документации OpenAI (JS):
    # const video = await openai.videos.create({ model: 'sora-2', prompt: '...' });
    # Далее — ожидание готовности через poll (аналог ручного опроса GET /videos/{id}).
    try:
        # JSON-тело: ProxyAPI не принимает urlencoded от SDK (multipart без файлов).
        video = await videos_create_json(
            openai_client,
            model=VIDEO_MODEL,
            prompt=prompt,
        )
        logger.info(
            "Video generation started: id=%s status=%s model=%s",
            video.id,
            video.status,
            video.model,
        )
        video = await openai_client.videos.poll(
            video.id,
            poll_interval_ms=3000,
        )
    except APIStatusError as e:
        if is_insufficient_funds_error(e):
            logger.warning(
                "video insufficient funds chat_id=%s status=%s body=%s",
                chat_id,
                e.status_code,
                e.body,
            )
            await notify_insufficient_funds(message, status_msg)
            return
        logger.exception("video API error chat_id=%s status=%s", chat_id, e.status_code)
        await status_msg.edit_text(f"Ошибка API видео ({e.status_code}): {e.message}")
        return
    except APIError as e:
        logger.exception("video create/poll APIError chat_id=%s", chat_id)
        await status_msg.edit_text(f"Ошибка API: {e.message}")
        return
    except Exception as e:
        logger.exception("video create/poll failed chat_id=%s", chat_id)
        await status_msg.edit_text(f"Ошибка генерации видео: {e}")
        return

    if video.status != "completed":
        err_msg = video.error.message if video.error else str(video.status)
        logger.error("video job not completed id=%s status=%s err=%s", video.id, video.status, err_msg)
        await status_msg.edit_text(_video_job_failure_text(err_msg))
        return

    try:
        sec = int(float(str(video.seconds)))
    except ValueError:
        sec = 4  # дефолт API, если длительность не распарсилась

    try:
        dl = await openai_client.videos.download_content(
            video.id,
            timeout=httpx.Timeout(300.0, connect=30.0),
        )
        data = dl.content
    except APIStatusError as e:
        if is_insufficient_funds_error(e):
            logger.warning("video download insufficient funds id=%s", video.id)
            await notify_insufficient_funds(message, status_msg)
            return
        logger.exception("video download API status id=%s", video.id)
        await status_msg.edit_text(f"Скачать видео не удалось ({e.status_code}): {e.message}")
        return
    except Exception as e:
        logger.exception("video download failed id=%s", video.id)
        await status_msg.edit_text(f"Видео сгенерировано, но скачать не удалось: {e}")
        return

    if len(data) > 50 * 1024 * 1024:
        logger.warning("video too large for Telegram id=%s bytes=%s", video.id, len(data))
        await status_msg.edit_text("Файл больше 50 МБ — отправка в Telegram невозможна.")
        return

    try:
        await status_msg.delete()
    except Exception as e:
        logger.debug("Не удалось удалить статус-сообщение: %s", e)

    cap = video_success_caption(prompt)
    await message.answer_video(
        BufferedInputFile(data, filename="sora.mp4"),
        caption=cap[:1024] if len(cap) > 1024 else cap,
    )

    usd_rub, cbr_date = await _usd_rub_safe()
    if usd_rub is not None:
        cost_html = format_video_cost_block(sec, usd_rub, cbr_date)
    else:
        cost_html = format_video_cost_block_no_rate(sec)
    await message.answer(cost_html, parse_mode="HTML")

    logger.info(
        "video branch ok chat_id=%s video_id=%s bytes=%s seconds=%s",
        chat_id,
        video.id,
        len(data),
        sec,
    )


async def run_image_generation(message: Message, prompt: str) -> None:
    """
    Отдельная ветка: GPT Image 1.5, quality=low (Images API).
    Идентификатор модели в OpenAI SDK: gpt-image-1.5 (см. types.image_model.ImageModel).
    """
    chat_id = message.chat.id
    logger.info(
        "image branch start chat_id=%s prompt_len=%s model=%s quality=%s size=%s",
        chat_id,
        len(prompt),
        IMAGE_MODEL,
        IMAGE_QUALITY,
        IMAGE_SIZE,
    )

    status_msg = await message.answer("Генерация изображения…")

    try:
        # Без response_format: у ProxyAPI параметр не поддерживается (400 unknown_parameter).
        resp = await openai_client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            quality=IMAGE_QUALITY,  # type: ignore[arg-type]
            size=IMAGE_SIZE,  # type: ignore[arg-type]
            n=1,
            timeout=httpx.Timeout(300.0, connect=60.0),
        )
    except APIStatusError as e:
        if is_insufficient_funds_error(e):
            logger.warning("image insufficient funds chat_id=%s status=%s", chat_id, e.status_code)
            await notify_insufficient_funds(message, status_msg)
            return
        logger.exception("image API error chat_id=%s status=%s", chat_id, e.status_code)
        await status_msg.edit_text(f"Ошибка API изображения ({e.status_code}): {e.message}")
        return
    except APIError as e:
        logger.exception("image generate APIError chat_id=%s", chat_id)
        await status_msg.edit_text(f"Ошибка API: {e.message}")
        return
    except Exception as e:
        logger.exception("image generate failed chat_id=%s", chat_id)
        await status_msg.edit_text(f"Ошибка генерации: {e}")
        return

    try:
        raw = await _image_bytes_from_response(resp)
    except ValueError as e:
        logger.error("image response parse chat_id=%s err=%s", chat_id, e)
        await status_msg.edit_text("Пустой или неожиданный ответ изображения от API.")
        return
    if len(raw) > 10 * 1024 * 1024:
        await status_msg.edit_text("Файл слишком большой для Telegram.")
        return

    usage = resp.usage
    usd_est = GPT_IMAGE_15_LOW_USD

    try:
        await status_msg.delete()
    except Exception as e:
        logger.debug("Не удалось удалить статус-сообщение (image): %s", e)

    cap = image_success_caption(prompt)
    await message.answer_photo(
        BufferedInputFile(raw, filename="gpt-image.png"),
        caption=cap[:1024] if len(cap) > 1024 else cap,
    )

    usd_rub, cbr_date = await _usd_rub_safe()
    if usd_rub is not None:
        cost_html = format_image_cost_block(usd_rub, usd_est, usage, cbr_date)
    else:
        cost_html = format_image_cost_block_no_rate(usd_est, usage)

    await message.answer(cost_html, parse_mode="HTML")
    logger.info("image branch ok chat_id=%s bytes=%s", chat_id, len(raw))


# ---------------------------------------------------------------------------
# Handlers: команды
# ---------------------------------------------------------------------------


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await MEMORY.ensure_chat(message.chat.id)
    mode_key = await MEMORY.get_mode(message.chat.id)
    entry = PROMPTS.prompts.get(mode_key) or PROMPTS.prompts[PROMPTS.default_prompt]
    await message.answer(
        "Привет! Режимы чата, память, видео (Sora) и картинки (GPT Image).\n\n"
        f"Текущий режим чата: <b>{entry.name}</b>\n\n"
        "💡 <i>С каждым новым запросом растёт число <b>входных токенов</b> и стоимость: "
        "в контекст передаётся история переписки.</i>\n\n"
        "/mode — режимы чата\n"
        "/reset — очистить историю\n"
        "/video — видео (или: /video описание сцены)\n"
        "/image — картинка (или: /image описание)\n"
        "/cancel — выйти из режима видео или картинки",
        parse_mode="HTML",
    )


@router.message(Command("mode"))
async def cmd_mode(message: Message) -> None:
    await MEMORY.ensure_chat(message.chat.id)
    lines = ["<b>Доступные режимы</b> (нажми кнопку ниже):\n"]
    for _key, entry in PROMPTS.prompts.items():
        lines.append(f"• <b>{entry.name}</b> — {entry.description}")
    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=_mode_keyboard(),
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    await MEMORY.reset(message.chat.id)
    await VIDEO_SESSION.clear(message.chat.id)
    await IMAGE_SESSION.clear(message.chat.id)
    await message.answer(
        "🧹 История диалога очищена.\n"
        "🎬🖼️ Режимы видео и картинки сброшены."
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    await VIDEO_SESSION.clear(message.chat.id)
    await IMAGE_SESSION.clear(message.chat.id)
    await message.answer(
        "✅ Режимы <b>видео</b> и <b>картинки</b> выключены. Можно снова писать в чат.",
        parse_mode="HTML",
    )


@router.message(Command("video"))
async def cmd_video(message: Message, command: CommandObject) -> None:
    await MEMORY.ensure_chat(message.chat.id)
    await IMAGE_SESSION.clear(message.chat.id)
    args = (command.args or "").strip()
    if args:
        logger.info("video command with inline prompt chat_id=%s len=%s", message.chat.id, len(args))
        await run_video_generation(message, args)
        return
    await VIDEO_SESSION.set_waiting(message.chat.id, True)
    await message.answer(
        "Режим <b>видео</b>: отправьте одним сообщением описание ролика.\n"
        "/cancel — выйти. Пример: «кот на скейтборде на закате»",
        parse_mode="HTML",
    )


@router.message(Command("image"))
async def cmd_image(message: Message, command: CommandObject) -> None:
    await MEMORY.ensure_chat(message.chat.id)
    await VIDEO_SESSION.clear(message.chat.id)
    args = (command.args or "").strip()
    if args:
        logger.info("image command with inline prompt chat_id=%s len=%s", message.chat.id, len(args))
        await run_image_generation(message, args)
        return
    await IMAGE_SESSION.set_waiting(message.chat.id, True)
    await message.answer(
        "Режим <b>картинки</b> (модель <code>gpt-image-1.5</code>, качество low): "
        "опишите изображение одним сообщением.\n"
        "/cancel — выйти.",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("mode:"))
async def callback_select_mode(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return
    key = callback.data.split(":", 1)[1]
    if key not in PROMPTS.prompts:
        await callback.answer("Неизвестный режим", show_alert=True)
        return
    chat_id = callback.message.chat.id
    logger.info("mode switch chat_id=%s key=%s", chat_id, key)
    await MEMORY.set_mode(chat_id, key)
    entry = PROMPTS.prompts[key]
    await callback.message.edit_text(
        f"✅ Режим изменён на: <b>{entry.name}</b>\n\n{entry.description}",
        parse_mode="HTML",
    )
    await callback.answer(f"Режим: {entry.name}")


# ---------------------------------------------------------------------------
# Handlers: текстовые сообщения
# ---------------------------------------------------------------------------


@router.message(F.text)
async def handle_text(message: Message) -> None:
    if not message.text:
        return
    chat_id = message.chat.id
    await MEMORY.ensure_chat(chat_id)

    if await VIDEO_SESSION.is_waiting(chat_id):
        prompt = message.text.strip()
        if len(prompt) < 5:
            await message.answer("Слишком коротко. Опишите сцену подробнее или /cancel.")
            return
        await VIDEO_SESSION.set_waiting(chat_id, False)
        await run_video_generation(message, prompt)
        return

    if await IMAGE_SESSION.is_waiting(chat_id):
        prompt = message.text.strip()
        if len(prompt) < 3:
            await message.answer("Слишком коротко. Опишите картинку или /cancel.")
            return
        await IMAGE_SESSION.set_waiting(chat_id, False)
        await run_image_generation(message, prompt)
        return

    logger.info("chat inbound chat_id=%s text_len=%s", chat_id, len(message.text))

    try:
        answer, usage = await _reply_openai(chat_id, message.text)
    except RuntimeError as e:
        msg = str(e)
        await message.answer(msg)
        if msg == MSG_INSUFFICIENT_FUNDS:
            logger.warning("chat user notified insufficient funds chat_id=%s", chat_id)
        return

    await MEMORY.append_user(chat_id, message.text)
    await MEMORY.append_assistant(chat_id, answer)
    await message.answer(answer)

    if usage is None:
        logger.warning("chat response without usage chat_id=%s", chat_id)
        return

    usd_rub, cbr_date = await _usd_rub_safe()
    if usd_rub is not None:
        cost_html = format_chat_cost_block(usage, usd_rub, cbr_date)
    else:
        cost_html = format_chat_cost_block_no_rate(usage)

    await message.answer(cost_html, parse_mode="HTML")
    logger.info(
        "chat done chat_id=%s prompt_tokens=%s completion_tokens=%s",
        chat_id,
        usage.prompt_tokens,
        usage.completion_tokens,
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


async def main() -> None:
    if not BOT_TOKEN or not OPENAI_API_KEY:
        logger.error("Задайте BOT_TOKEN и OPENAI_API_KEY (или PROXYAPI_API_KEY) в .env")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info(
        "Старт polling: chat=%s video=%s image=%s base_url=%s memory=%s",
        OPENAI_MODEL,
        VIDEO_MODEL,
        IMAGE_MODEL,
        OPENAI_BASE_URL,
        MEMORY_MAX_MESSAGES,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
