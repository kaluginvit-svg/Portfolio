"""
Расчёт стоимости запросов в USD и рублях (по тарифам из config и курсу ЦБ).
Форматирование сообщений — в стиле «юзабилити» (блоки с эмодзи).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai.types.completion_usage import CompletionUsage
    from openai.types.images_response import Usage as ImageGenUsage

from config import (
    PRICE_OUTPUT_PER_1M_USD,
    PRICE_INPUT_PER_1M_USD,
    SORA2_USD_PER_SECOND,
)


def _cbr_date_line(cbr_date: str | None) -> str:
    """Строка с датой установки курса в выгрузке ЦБ (DD.MM.YYYY)."""
    if not cbr_date:
        return ""
    return f"\n📅 <b>Дата курса ЦБ:</b> {cbr_date}"


def _fmt_usd_small(amount: Decimal) -> str:
    """Компактный вывод малых сумм в USD (как в референсе ~$0.000019)."""
    s = f"{amount:.8f}".rstrip("0").rstrip(".")
    return s if s else "0"


def chat_cost_usd(usage: "CompletionUsage") -> Decimal:
    pt = usage.prompt_tokens or 0
    ct = usage.completion_tokens or 0
    return (
        Decimal(pt) / Decimal(1_000_000) * PRICE_INPUT_PER_1M_USD
        + Decimal(ct) / Decimal(1_000_000) * PRICE_OUTPUT_PER_1M_USD
    )


def video_cost_usd_estimate(seconds: int) -> Decimal:
    return Decimal(seconds) * SORA2_USD_PER_SECOND


def format_chat_cost_block(
    usage: "CompletionUsage",
    usd_rub: Decimal,
    cbr_date: str | None = None,
) -> str:
    """Блок «Стоимость запроса» после ответа в чате (HTML)."""
    pt = usage.prompt_tokens or 0
    ct = usage.completion_tokens or 0
    usd = chat_cost_usd(usage)
    rub = (usd * usd_rub).quantize(Decimal("0.01"))
    usd_s = _fmt_usd_small(usd)
    return (
        "💰 <b>Стоимость запроса:</b>\n"
        f"📥 <b>Входные токены:</b> {pt}\n"
        f"📤 <b>Выходные токены:</b> {ct}\n"
        f"💵 <b>Стоимость:</b> ~${usd_s} (~{rub} ₽, курс ЦБ ≈{usd_rub:.2f} ₽/$)"
        f"{_cbr_date_line(cbr_date)}"
    )


def format_chat_cost_block_no_rate(usage: "CompletionUsage") -> str:
    pt = usage.prompt_tokens or 0
    ct = usage.completion_tokens or 0
    usd = chat_cost_usd(usage)
    usd_s = _fmt_usd_small(usd)
    return (
        "💰 <b>Стоимость запроса:</b>\n"
        f"📥 <b>Входные токены:</b> {pt}\n"
        f"📤 <b>Выходные токены:</b> {ct}\n"
        f"💵 <b>Стоимость:</b> ~${usd_s}\n"
        "<i>Курс ЦБ временно недоступен — сумма в ₽ не показана.</i>"
    )


def format_image_cost_block(
    usd_rub: Decimal,
    usd_estimate: Decimal,
    usage: "ImageGenUsage | None" = None,
    cbr_date: str | None = None,
) -> str:
    """Второе сообщение после картинки — стоимость (HTML)."""
    rub = (usd_estimate * usd_rub).quantize(Decimal("0.01"))
    lines = [
        "💰 <b>Стоимость запроса (оценка):</b>",
        f"💵 ~${ _fmt_usd_small(usd_estimate) } (~{rub} ₽, курс ЦБ ≈{usd_rub:.2f} ₽/$)",
    ]
    if usage is not None:
        lines.append(f"📥 <b>Входные токены (API):</b> {usage.input_tokens}")
        lines.append(f"📤 <b>Выходные токены (API):</b> {usage.output_tokens}")
        lines.append(f"📊 <b>Всего токенов:</b> {usage.total_tokens}")
    body = "\n".join(lines)
    return body + _cbr_date_line(cbr_date)


def format_image_cost_block_no_rate(
    usd_estimate: Decimal,
    usage: "ImageGenUsage | None" = None,
) -> str:
    lines = [
        "💰 <b>Стоимость запроса (оценка):</b>",
        f"💵 ~${ _fmt_usd_small(usd_estimate) }",
        "<i>Курс ЦБ временно недоступен.</i>",
    ]
    if usage is not None:
        lines.append(f"📥 <b>Входные токены (API):</b> {usage.input_tokens}")
        lines.append(f"📤 <b>Выходные токены (API):</b> {usage.output_tokens}")
        lines.append(f"📊 <b>Всего токенов:</b> {usage.total_tokens}")
    return "\n".join(lines)


def format_video_cost_block(
    seconds: int,
    usd_rub: Decimal,
    cbr_date: str | None = None,
) -> str:
    usd = video_cost_usd_estimate(seconds)
    rub = (usd * usd_rub).quantize(Decimal("0.01"))
    return (
        "💰 <b>Стоимость запроса (оценка):</b>\n"
        f"⏱ <b>Длительность:</b> ~{seconds} с\n"
        f"💵 <b>Стоимость:</b> ~${ _fmt_usd_small(usd) } (~{rub} ₽, курс ЦБ ≈{usd_rub:.2f} ₽/$)"
        f"{_cbr_date_line(cbr_date)}"
    )


def format_video_cost_block_no_rate(seconds: int) -> str:
    usd = video_cost_usd_estimate(seconds)
    return (
        "💰 <b>Стоимость запроса (оценка):</b>\n"
        f"⏱ <b>Длительность:</b> ~{seconds} с\n"
        f"💵 <b>Стоимость:</b> ~${ _fmt_usd_small(usd) }\n"
        "<i>Курс ЦБ временно недоступен.</i>"
    )


def image_success_caption(prompt: str, max_len: int = 700) -> str:
    """Подпись к фото по референсу (plain text, без HTML)."""
    p = prompt.replace("\n", " ").strip()
    if len(p) > max_len:
        p = p[: max_len - 1] + "…"
    return (
        "🖼️ ✅ Изображение успешно сгенерировано!\n"
        f"📝 Описание: {p}\n"
        "🖼️ Изображение готово!"
    )


def video_success_caption(prompt: str, max_len: int = 700) -> str:
    """Подпись к видео в том же стиле (plain text)."""
    p = prompt.replace("\n", " ").strip()
    if len(p) > max_len:
        p = p[: max_len - 1] + "…"
    return (
        "🎬 ✅ Видео успешно сгенерировано!\n"
        f"📝 Описание: {p}\n"
        "🎬 Видео готово!"
    )
