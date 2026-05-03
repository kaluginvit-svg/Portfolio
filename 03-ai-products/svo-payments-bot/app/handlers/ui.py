"""Редактирование одного экрана диалога."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext

log = logging.getLogger(__name__)


async def edit_or_send(
    anchor: Message,
    *,
    text: str,
    reply_markup: InlineKeyboardMarkup | None,
    state: "FSMContext",
) -> None:
    data = await state.get_data()
    mid = data.get("ui_message_id")
    bot = anchor.bot
    chat_id = anchor.chat.id
    if mid:
        try:
            await bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=mid,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                return
            log.debug("edit_message_text: %s", e)
    msg = await anchor.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.update_data(ui_message_id=msg.message_id)
