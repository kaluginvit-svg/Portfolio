"""Состояния FSM анкеты."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class QuestionnaireStates(StatesGroup):
    choose_scenario = State()
    deceased = State()
    applicant = State()
    complex_detail = State()
    recipients = State()
    recipients_many = State()
    documents = State()
    problem = State()
    submitted = State()
    waiting = State()
    region = State()
    result = State()
    lead_name = State()
    lead_phone = State()
    lead_contact = State()
    lead_comment = State()
    consent = State()
    consent_refused = State()


_ORDER: tuple[State, ...] = (
    QuestionnaireStates.choose_scenario,
    QuestionnaireStates.deceased,
    QuestionnaireStates.applicant,
    QuestionnaireStates.complex_detail,
    QuestionnaireStates.recipients,
    QuestionnaireStates.recipients_many,
    QuestionnaireStates.documents,
    QuestionnaireStates.problem,
    QuestionnaireStates.submitted,
    QuestionnaireStates.waiting,
    QuestionnaireStates.region,
    QuestionnaireStates.result,
    QuestionnaireStates.lead_name,
    QuestionnaireStates.lead_phone,
    QuestionnaireStates.lead_contact,
    QuestionnaireStates.lead_comment,
    QuestionnaireStates.consent,
    QuestionnaireStates.consent_refused,
)

STATE_BY_KEY: dict[str, State] = {s.state: s for s in _ORDER}


def state_from_key(key: str | None) -> State | None:
    if not key:
        return None
    return STATE_BY_KEY.get(key)
