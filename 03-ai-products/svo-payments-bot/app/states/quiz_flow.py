"""FSM квизов (отдельно от анкеты)."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class QuizFlowStates(StatesGroup):
    question = State()
    lead_name = State()
    lead_phone = State()
    consent = State()
    consent_refused = State()
