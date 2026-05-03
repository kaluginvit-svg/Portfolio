"""Сценарий A: документы (multi-select)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.handlers.common import _go, _persist
from app.handlers.render import show_step
from app.keyboards.questionnaire import DOC_KEYS
from app.repositories.lead_repository import LeadRepository
from app.states.questionnaire import QuestionnaireStates as Q

router = Router()


@router.callback_query(StateFilter(Q.documents), F.data.startswith("dc:"))
async def step_documents(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    if not call.from_user or not call.message:
        return
    uid = call.from_user.id
    raw = (call.data or "").split(":")[-1]
    data = await state.get_data()

    if raw == "done":
        await call.answer()
        await _go(call.message, state, repo, uid, Q.region)
        return

    if raw not in DOC_KEYS:
        await call.answer()
        return

    await call.answer("Ок")
    docs = list(data.get("selected_documents") or [])
    s = set(docs)
    if raw in s:
        s.remove(raw)
    else:
        s.add(raw)
    await state.update_data(selected_documents=sorted(s))
    await show_step(call.message, state, Q.documents)
    await _persist(state, repo, uid)
