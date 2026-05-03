"""Сообщения вне ожидаемого ввода."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.states.questionnaire import QuestionnaireStates as Q
from app.states.quiz_flow import QuizFlowStates as Z
from app.texts import messages

log = logging.getLogger(__name__)
router = Router()


@router.message(StateFilter(None), F.chat.type == "private", F.text)
async def no_state(message: Message) -> None:
    await message.answer(
        "Нажмите /start, чтобы открыть анкету предварительного расчёта и при необходимости оформить заявку.",
        parse_mode="HTML",
    )


TEXT_EXPECTING_STATES = (
    Q.recipients_many,
    Q.region,
    Q.lead_name,
    Q.lead_phone,
    Q.lead_contact,
    Q.lead_comment,
    Z.lead_name,
    Z.lead_phone,
)


@router.message(
    StateFilter(*TEXT_EXPECTING_STATES),
    ~F.text,
    F.chat.type == "private",
)
async def wrong_content_type(message: Message) -> None:
    await message.answer(messages.fallback_hint(), parse_mode="HTML")


@router.message(
    ~StateFilter(None),
    ~StateFilter(Q.choose_scenario),
    ~StateFilter(Z.question),
    ~StateFilter(*TEXT_EXPECTING_STATES),
    F.chat.type == "private",
    F.text,
)
async def text_instead_of_buttons(message: Message, state: FSMContext) -> None:
    st = await state.get_state()
    log.debug("Текст вместо кнопок state=%s user=%s", st, message.from_user.id if message.from_user else None)
    await message.answer(messages.fallback_hint(), parse_mode="HTML")
