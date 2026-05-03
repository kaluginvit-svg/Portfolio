"""Куда ведёт «Назад» в зависимости от состояния и сценария."""

from __future__ import annotations

from typing import Any

from app.states.questionnaire import QuestionnaireStates as Q


def previous_state_str(current: str | None, data: dict[str, Any]) -> str | None:
    if not current:
        return None
    scenario = data.get("scenario")

    if current == Q.consent.state:
        return Q.lead_comment.state
    if current == Q.lead_comment.state:
        return Q.lead_contact.state
    if current == Q.lead_contact.state:
        return Q.lead_phone.state
    if current == Q.lead_phone.state:
        return Q.lead_name.state
    if current == Q.lead_name.state:
        return Q.result.state

    if current == Q.result.state:
        return Q.region.state

    if current == Q.region.state:
        if scenario == "first_time":
            return Q.documents.state
        return Q.waiting.state

    if current == Q.documents.state:
        if data.get("recipients_was_many"):
            return Q.recipients_many.state
        return Q.recipients.state

    if current == Q.waiting.state:
        return Q.submitted.state
    if current == Q.submitted.state:
        return Q.problem.state
    if current == Q.problem.state:
        return Q.recipients.state

    if current == Q.recipients_many.state:
        return Q.recipients.state

    if current == Q.recipients.state:
        if data.get("applicant_role") == "complex" and data.get("complex_status"):
            return Q.complex_detail.state
        return Q.applicant.state

    if current == Q.complex_detail.state:
        return Q.applicant.state

    if current == Q.applicant.state:
        return Q.deceased.state

    if current == Q.deceased.state:
        return Q.choose_scenario.state

    return None
