"""Команды /start, /help, /restart."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.handlers.render import show_step
from app.repositories.lead_repository import LeadRepository
from app.services import progress_service
from app.states.questionnaire import QuestionnaireStates as Q, state_from_key
from app.texts import messages

log = logging.getLogger(__name__)
router = Router()


def _user_meta(message: Message) -> dict:
    u = message.from_user
    if not u:
        return {}
    return {
        "telegram_user_id": u.id,
        "telegram_username": u.username,
    }


async def _sync(state: FSMContext, repo: LeadRepository, uid: int) -> None:
    d = await state.get_data()
    st = await state.get_state()
    await progress_service.sync_progress_with_state(repo, uid, data=d, fsm_state=st)


@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(
    message: Message,
    state: FSMContext,
    repo: LeadRepository,
) -> None:
    await state.clear()
    meta = _user_meta(message)
    uid = meta.get("telegram_user_id")
    if uid is None:
        return

    record = await repo.get_incomplete(uid)
    resume_later = False
    if record and record.wizard_state and record.scenario:
        st = state_from_key(record.wizard_state)
        if st and st != Q.choose_scenario:
            resume_later = True

    await state.update_data(**meta, draft_resume_available=resume_later)
    await state.set_state(Q.choose_scenario)
    await show_step(message, state, Q.choose_scenario)
    await _sync(state, repo, uid)
    log.info("start user=%s", uid)


@router.message(Command("help"), F.chat.type == "private")
async def cmd_help(message: Message) -> None:
    await message.answer(messages.help_text(), parse_mode="HTML")


@router.message(Command("restart"), F.chat.type == "private")
async def cmd_restart(
    message: Message,
    state: FSMContext,
    repo: LeadRepository,
) -> None:
    await state.clear()
    meta = _user_meta(message)
    uid = meta.get("telegram_user_id")
    if uid is not None:
        await repo.delete_incomplete(uid)
    await state.update_data(**meta)
    await state.set_state(Q.choose_scenario)
    await show_step(message, state, Q.choose_scenario)
    if uid is not None:
        await _sync(state, repo, uid)
    log.info("restart user=%s", uid)
