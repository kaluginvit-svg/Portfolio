"""Экран результата: переход к заявке или повторный расчёт."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.handlers.common import _go
from app.handlers.render import show_step
from app.repositories.lead_repository import LeadRepository
from app.states.questionnaire import QuestionnaireStates as Q

router = Router()


@router.callback_query(StateFilter(Q.result), F.data == "rs:lead")
async def result_to_lead(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    if not call.message or not call.from_user:
        return
    await _go(call.message, state, repo, call.from_user.id, Q.lead_name)


@router.callback_query(StateFilter(Q.result), F.data == "rs:again")
async def result_restart(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    if not call.from_user or not call.message:
        return
    uid = call.from_user.id
    await repo.delete_incomplete(uid)
    data = await state.get_data()
    keep = {
        k: data[k]
        for k in ("telegram_user_id", "telegram_username", "ui_message_id")
        if k in data
    }
    await state.set_data(keep)
    await _go(call.message, state, repo, uid, Q.choose_scenario)
