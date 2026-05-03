"""Отрисовка текущего шага анкеты."""

from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import InlineKeyboardMarkup, Message

from app.handlers.ui import edit_or_send
from app.keyboards import questionnaire as kb
from app.states.questionnaire import QuestionnaireStates as Q
from app.texts import messages


def _keyboard_for(state: State, data: dict) -> InlineKeyboardMarkup | None:
    if state == Q.choose_scenario:
        return kb.scenario_choice(show_resume=bool(data.get("draft_resume_available")))
    if state == Q.deceased:
        return kb.deceased_status()
    if state == Q.applicant:
        return kb.applicant_role()
    if state == Q.complex_detail:
        return kb.complex_status()
    if state == Q.recipients:
        return kb.recipients()
    if state == Q.recipients_many:
        return kb.region_only_nav()
    if state == Q.documents:
        return kb.documents(set(data.get("selected_documents") or []))
    if state == Q.problem:
        return kb.problem_type()
    if state == Q.submitted:
        return kb.submitted_to()
    if state == Q.waiting:
        return kb.waiting()
    if state == Q.region:
        return kb.region_only_nav()
    if state == Q.result:
        return kb.result_actions()
    if state == Q.lead_name:
        return kb.lead_name_nav()
    if state == Q.lead_phone:
        return kb.lead_phone_nav()
    if state == Q.lead_contact:
        return kb.lead_skip_contact()
    if state == Q.lead_comment:
        return kb.lead_skip_comment()
    if state == Q.consent:
        return kb.consent()
    return None


async def show_step(anchor: Message, state: FSMContext, st: State) -> None:
    data = await state.get_data()
    if st == Q.choose_scenario:
        show_resume = bool(data.get("draft_resume_available"))
        text = messages.welcome(has_saved_questionnaire=show_resume)
        markup = kb.scenario_choice(show_resume=show_resume)
        await edit_or_send(anchor, text=text, reply_markup=markup, state=state)
        return
    if st == Q.result:
        text = messages.result_screen(data)
        markup = _keyboard_for(st, data)
    elif st == Q.consent_refused:
        text = messages.question_text(st, data)
        markup = kb.consent_refused()
    else:
        text = messages.question_text(st, data)
        markup = _keyboard_for(st, data)
    await edit_or_send(anchor, text=text, reply_markup=markup, state=state)
