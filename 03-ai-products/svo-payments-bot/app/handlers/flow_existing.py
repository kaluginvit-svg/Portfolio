"""Сценарий B: проблема, куда подавали, срок ожидания."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.handlers.common import PR_MAP, SU_MAP, WT_MAP, _go
from app.repositories.lead_repository import LeadRepository
from app.states.questionnaire import QuestionnaireStates as Q

router = Router()


@router.callback_query(StateFilter(Q.problem), F.data.startswith("pr:"))
async def step_problem(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    raw = (call.data or "").split(":")[-1]
    if raw not in PR_MAP or not call.message or not call.from_user:
        return
    await state.update_data(problem_type=PR_MAP[raw])
    await _go(call.message, state, repo, call.from_user.id, Q.submitted)


@router.callback_query(StateFilter(Q.submitted), F.data.startswith("su:"))
async def step_submitted(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    raw = (call.data or "").split(":")[-1]
    if raw not in SU_MAP or not call.message or not call.from_user:
        return
    await state.update_data(submitted_to=SU_MAP[raw])
    await _go(call.message, state, repo, call.from_user.id, Q.waiting)


@router.callback_query(StateFilter(Q.waiting), F.data.startswith("wt:"))
async def step_waiting(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    raw = (call.data or "").split(":")[-1]
    if raw not in WT_MAP or not call.message or not call.from_user:
        return
    await state.update_data(waiting_key=raw, months_waiting=WT_MAP[raw])
    await _go(call.message, state, repo, call.from_user.id, Q.region)
