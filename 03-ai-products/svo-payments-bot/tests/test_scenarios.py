"""Сценарные проверки: навигация «Назад», состояния FSM, экран результата, быстрый цикл БД."""

from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path

import pytest

from app.db.base import init_db
from app.handlers.navigation import previous_state_str
from app.repositories.lead_repository import LeadRepository
from app.services import progress_service
from app.states.questionnaire import QuestionnaireStates as Q, state_from_key
from app.texts import messages


def _walk_back(start: str, data: dict) -> list[str]:
    out: list[str] = []
    cur: str | None = start
    seen: set[str] = set()
    while cur and cur not in seen:
        seen.add(cur)
        out.append(cur)
        cur = previous_state_str(cur, data)
    return out


def test_state_from_key_covers_all_questionnaire_states() -> None:
    for st in (
        Q.choose_scenario,
        Q.deceased,
        Q.applicant,
        Q.complex_detail,
        Q.recipients,
        Q.recipients_many,
        Q.documents,
        Q.problem,
        Q.submitted,
        Q.waiting,
        Q.region,
        Q.result,
        Q.lead_name,
        Q.lead_phone,
        Q.lead_contact,
        Q.lead_comment,
        Q.consent,
        Q.consent_refused,
    ):
        assert state_from_key(st.state) == st


def test_back_chain_first_time_simple() -> None:
    data = {
        "scenario": "first_time",
        "recipients_was_many": False,
        "applicant_role": "spouse",
        "complex_status": None,
    }
    chain = _walk_back(Q.result.state, data)
    assert chain[0] == Q.result.state
    assert Q.region.state in chain
    assert Q.documents.state in chain
    assert Q.recipients.state in chain
    assert Q.applicant.state in chain
    assert Q.deceased.state in chain
    assert chain[-1] == Q.choose_scenario.state


def test_back_chain_first_time_complex_applicant() -> None:
    data = {
        "scenario": "first_time",
        "recipients_was_many": False,
        "applicant_role": "complex",
        "complex_status": "unregistered_cohabitation",
    }
    chain = _walk_back(Q.result.state, data)
    assert Q.complex_detail.state in chain
    assert chain[-1] == Q.choose_scenario.state


def test_back_chain_first_time_recipients_many() -> None:
    data = {
        "scenario": "first_time",
        "recipients_was_many": True,
        "applicant_role": "mother",
    }
    chain = _walk_back(Q.result.state, data)
    assert Q.recipients_many.state in chain
    assert chain[-1] == Q.choose_scenario.state


def test_back_chain_already_filed() -> None:
    data = {
        "scenario": "already_filed",
        "recipients_was_many": False,
        "applicant_role": "father",
    }
    chain = _walk_back(Q.result.state, data)
    assert Q.waiting.state in chain
    assert Q.submitted.state in chain
    assert Q.problem.state in chain
    assert Q.documents.state not in chain
    assert chain[-1] == Q.choose_scenario.state


def test_back_chain_lead_form() -> None:
    data: dict = {}
    chain = _walk_back(Q.consent.state, data)
    expected = [
        Q.consent.state,
        Q.lead_comment.state,
        Q.lead_contact.state,
        Q.lead_phone.state,
        Q.lead_name.state,
        Q.result.state,
    ]
    assert chain[: len(expected)] == expected


def test_result_screen_first_time_renders() -> None:
    text = messages.result_screen(
        {
            "scenario": "first_time",
            "recipients_count": 2,
            "applicant_role": "spouse",
            "status_of_deceased": "contract",
        }
    )
    assert "Предварительный расчёт" in text
    assert "14" in text


def test_result_screen_already_filed_renders() -> None:
    text = messages.result_screen(
        {
            "scenario": "already_filed",
            "recipients_count": 1,
            "applicant_role": "mother",
            "months_waiting": 3,
            "waiting_key": "w4",
        }
    )
    assert "Предварительный расчёт" in text
    assert "ожидание" in text.lower()


@pytest.mark.asyncio
async def test_repo_sync_cycle_is_fast() -> None:
    """Много коротких записей в leads — не должно «тормозить» заметно на локальном SQLite."""
    path = Path(tempfile.gettempdir()) / "svo_scenario_perf.db"
    path.unlink(missing_ok=True)
    await init_db(path)
    repo = LeadRepository(path)
    await repo.create_draft(
        telegram_user_id=999001,
        telegram_username=None,
        telegram_first_name=None,
        scenario="first_time",
    )
    t0 = time.perf_counter()
    for i in range(40):
        await progress_service.sync_progress_with_state(
            repo,
            999001,
            data={"region": f"R{i}", "recipients_count": 2},
            fsm_state=Q.region.state,
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < 3.0, f"40× sync заняли {elapsed:.2f}s, ожидалось < 3s"


@pytest.mark.asyncio
async def test_parallel_repo_updates_different_users() -> None:
    path = Path(tempfile.gettempdir()) / "svo_scenario_parallel.db"
    path.unlink(missing_ok=True)
    await init_db(path)
    repo = LeadRepository(path)
    for uid in (10, 11):
        await repo.create_draft(
            telegram_user_id=uid,
            telegram_username=None,
            telegram_first_name=None,
            scenario="first_time",
        )

    async def bump(uid: int) -> None:
        for _ in range(15):
            await progress_service.sync_progress(repo, uid, {"recipients_count": 3})

    t0 = time.perf_counter()
    await asyncio.gather(bump(10), bump(11))
    elapsed = time.perf_counter() - t0
    assert elapsed < 2.5, f"параллельные записи {elapsed:.2f}s"
