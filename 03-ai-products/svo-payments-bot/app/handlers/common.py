"""Общие шаги анкеты, навигация, регион и расчёт."""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message

from app.handlers.navigation import previous_state_str
from app.handlers.render import show_step
from app.repositories.lead_repository import LeadRepository
from app.services import calculator as calc
from app.services import progress_service
from app.states.questionnaire import QuestionnaireStates as Q, state_from_key
from app.texts import messages

router = Router()


async def _persist(state: FSMContext, repo: LeadRepository, uid: int) -> None:
    d = await state.get_data()
    st = await state.get_state()
    await progress_service.sync_progress_with_state(repo, uid, data=d, fsm_state=st)


async def _go(anchor: Message, state: FSMContext, repo: LeadRepository, uid: int, st: State) -> None:
    await state.set_state(st)
    await show_step(anchor, state, st)
    await _persist(state, repo, uid)


DE_MAP = {
    "contract": "contract",
    "mob": "mobilized",
    "vol": "volunteer",
    "rg": "rosgvard",
    "unk": "unknown",
}

AP_MAP = {
    "spouse": "spouse",
    "mother": "mother",
    "father": "father",
    "c18": "child_u18",
    "st": "child_student",
    "rep": "representative",
}

CX_MAP = {"coh": "unregistered_cohabitation", "kin": "kinship_dispute", "hlp": "need_status_help"}

PR_MAP = {
    "none": "no_response",
    "inc": "incomplete",
    "rej": "rejected",
    "part": "partial",
    "stuck": "stuck",
}

SU_MAP = {
    "unit": "military_unit",
    "vk": "voenkomat",
    "sog": "sogaz",
    "sfr": "sfr_mfc",
    "multi": "multiple",
}

WT_MAP = {"w1": 1, "w2": 2, "w4": 4, "w6": 6}


@router.callback_query(StateFilter(Q.choose_scenario), F.data == "draft:resume")
async def resume_questionnaire_draft(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    if not call.from_user or not call.message:
        return
    uid = call.from_user.id
    u = call.from_user
    record = await repo.get_incomplete(uid)
    if not record or not record.wizard_state or not record.scenario:
        await state.update_data(draft_resume_available=False)
        await _go(call.message, state, repo, uid, Q.choose_scenario)
        return
    st = state_from_key(record.wizard_state)
    if not st or st == Q.choose_scenario:
        await state.update_data(draft_resume_available=False)
        await _go(call.message, state, repo, uid, Q.choose_scenario)
        return
    merged = progress_service.restore_fsm_from_lead(record)
    merged.update(
        {
            "telegram_user_id": uid,
            "telegram_username": u.username,
            "draft_resume_available": False,
        }
    )
    mid = (await state.get_data()).get("ui_message_id")
    if mid is not None:
        merged["ui_message_id"] = mid
    await state.set_data(merged)
    await state.set_state(st)
    await show_step(call.message, state, st)
    await _persist(state, repo, uid)


@router.callback_query(StateFilter(Q.choose_scenario), F.data.startswith("sc:"))
async def pick_scenario(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    if not call.from_user or not call.message:
        return
    await call.answer()
    uid = call.from_user.id
    u = call.from_user
    await repo.delete_incomplete(uid)
    await repo.create_draft(
        telegram_user_id=uid,
        telegram_username=u.username,
        telegram_first_name=None,
        scenario="first_time" if call.data == "sc:first" else "already_filed",
    )
    scenario = "first_time" if call.data == "sc:first" else "already_filed"
    base = {k: v for k, v in (await state.get_data()).items() if k.startswith("telegram_") or k == "ui_message_id"}
    await state.set_data(
        {
            **base,
            "scenario": scenario,
            "selected_documents": [],
            "recipients_was_many": False,
            "status_of_deceased": None,
            "applicant_role": None,
            "complex_status": None,
            "recipients_count": None,
            "problem_type": None,
            "submitted_to": None,
            "months_waiting": None,
            "waiting_key": None,
            "region": None,
        }
    )
    await _go(call.message, state, repo, uid, Q.deceased)


@router.callback_query(F.data == "nav:home")
async def nav_home(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
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


@router.callback_query(F.data == "nav:back")
async def nav_back(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    if not call.from_user or not call.message:
        return
    cur = await state.get_state()
    data = await state.get_data()
    prev = previous_state_str(cur, data)
    if not prev:
        await call.answer("Назад недоступен: это начало анкеты")
        return
    await call.answer()
    uid = call.from_user.id

    if prev == Q.choose_scenario.state:
        await repo.delete_incomplete(uid)

    if prev == Q.applicant.state and cur == Q.complex_detail.state:
        await state.update_data(applicant_role=None, complex_status=None)

    if prev == Q.applicant.state and cur == Q.recipients.state:
        await state.update_data(recipients_count=None, recipients_was_many=False)

    if prev == Q.recipients.state and cur == Q.recipients_many.state:
        await state.update_data(recipients_count=None)

    if prev == Q.recipients.state and cur == Q.documents.state:
        await state.update_data(selected_documents=[])

    if prev == Q.recipients.state and cur == Q.problem.state:
        await state.update_data(problem_type=None)

    if prev == Q.problem.state and cur == Q.submitted.state:
        await state.update_data(submitted_to=None)

    if prev == Q.submitted.state and cur == Q.waiting.state:
        await state.update_data(months_waiting=None, waiting_key=None)

    if prev in (Q.documents.state, Q.waiting.state) and cur == Q.region.state:
        await state.update_data(
            region=None,
            base_total=None,
            personal_share=None,
            child_monthly_payment_applicable=None,
            estimated_lost_income=None,
        )

    if prev == Q.region.state and cur == Q.result.state:
        pass

    if prev == Q.result.state and cur == Q.lead_name.state:
        await state.update_data(lead_name=None)

    if prev == Q.lead_name.state and cur == Q.lead_phone.state:
        await state.update_data(phone=None, normalized_phone=None)

    if prev == Q.lead_phone.state and cur == Q.lead_contact.state:
        await state.update_data(contact_method=None)

    if prev == Q.lead_contact.state and cur == Q.lead_comment.state:
        await state.update_data(comment=None)

    if prev == Q.deceased.state and cur == Q.applicant.state:
        await state.update_data(status_of_deceased=None)

    prev_st = state_from_key(prev)
    if not prev_st:
        return
    await state.set_state(prev_st)
    await show_step(call.message, state, prev_st)
    await _persist(state, repo, uid)


@router.callback_query(StateFilter(Q.deceased), F.data.startswith("de:"))
async def step_deceased(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    key = (call.data or "").split(":")[-1]
    if key not in DE_MAP or not call.message or not call.from_user:
        return
    await state.update_data(status_of_deceased=DE_MAP[key])
    await _go(call.message, state, repo, call.from_user.id, Q.applicant)


@router.callback_query(StateFilter(Q.applicant), F.data.startswith("ap:"))
async def step_applicant(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    if not call.message or not call.from_user:
        return
    raw = (call.data or "").split(":")[-1]
    if raw == "complex":
        await state.update_data(applicant_role="complex", complex_status=None)
        await _go(call.message, state, repo, call.from_user.id, Q.complex_detail)
        return
    if raw not in AP_MAP:
        return
    await state.update_data(applicant_role=AP_MAP[raw], complex_status=None)
    await _go(call.message, state, repo, call.from_user.id, Q.recipients)


@router.callback_query(StateFilter(Q.complex_detail), F.data.startswith("cx:"))
async def step_complex(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    raw = (call.data or "").split(":")[-1]
    if raw not in CX_MAP or not call.message or not call.from_user:
        return
    await state.update_data(applicant_role="complex", complex_status=CX_MAP[raw])
    await _go(call.message, state, repo, call.from_user.id, Q.recipients)


@router.callback_query(StateFilter(Q.recipients), F.data.startswith("rc:"))
async def step_recipients(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    if not call.message or not call.from_user:
        return
    raw = (call.data or "").split(":")[-1]
    data = await state.get_data()
    scenario = data.get("scenario")
    if raw == "many":
        await state.update_data(recipients_was_many=True, recipients_count=None)
        await _go(call.message, state, repo, call.from_user.id, Q.recipients_many)
        return
    if raw not in ("1", "2", "3", "4"):
        return
    await state.update_data(recipients_was_many=False, recipients_count=int(raw))
    if scenario == "first_time":
        await state.update_data(selected_documents=[])
        await _go(call.message, state, repo, call.from_user.id, Q.documents)
    else:
        await _go(call.message, state, repo, call.from_user.id, Q.problem)


@router.message(StateFilter(Q.recipients_many), F.text)
async def step_recipients_many_text(message: Message, state: FSMContext, repo: LeadRepository) -> None:
    if not message.from_user:
        return
    m = re.fullmatch(r"\s*(\d{1,2})\s*", message.text or "")
    if not m:
        await message.answer(messages.recipients_count_invalid(), parse_mode="HTML")
        return
    n = int(m.group(1))
    if n < 5 or n > 30:
        await message.answer(messages.recipients_count_invalid(), parse_mode="HTML")
        return
    data = await state.get_data()
    scenario = data.get("scenario")
    await state.update_data(recipients_count=n, recipients_was_many=True)
    if scenario == "first_time":
        await state.update_data(selected_documents=[])
        await _go(message, state, repo, message.from_user.id, Q.documents)
    else:
        await _go(message, state, repo, message.from_user.id, Q.problem)


@router.message(StateFilter(Q.region), F.text)
async def step_region(message: Message, state: FSMContext, repo: LeadRepository) -> None:
    if not message.from_user:
        return
    region = (message.text or "").strip()
    if not region:
        await message.answer(messages.region_invalid(), parse_mode="HTML")
        return
    data = await state.get_data()
    rc = int(data.get("recipients_count") or 1)
    role = data.get("applicant_role")
    scenario = data.get("scenario")
    base_total = calc.get_base_total()
    personal_share = calc.get_personal_share(rc)
    child_ok = calc.has_child_monthly_payment(role)
    months = data.get("months_waiting")
    lost = None
    if scenario == "already_filed" and months is not None:
        lost = calc.calculate_lost_income(personal_share, int(months))
    await state.update_data(
        region=region,
        base_total=base_total,
        personal_share=personal_share,
        child_monthly_payment_applicable=child_ok,
        estimated_lost_income=lost,
    )
    await _go(message, state, repo, message.from_user.id, Q.result)


@router.message(StateFilter(Q.choose_scenario), F.text, F.chat.type == "private")
async def choose_scenario_text(message: Message) -> None:
    await message.answer(
        "Пожалуйста, выберите вариант кнопками под сообщением бота или нажмите /restart.",
        parse_mode="HTML",
    )
