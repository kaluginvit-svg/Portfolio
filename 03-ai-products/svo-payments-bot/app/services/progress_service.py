"""Синхронизация ответов пользователя с черновиком в БД."""

from __future__ import annotations

from typing import Any

from app.db.models import LeadRecord
from app.repositories.lead_repository import LeadRepository


def fsm_to_lead_patch(data: dict[str, Any]) -> dict[str, Any]:
    """Поля FSM data -> колонки leads (только известные ключи)."""
    patch: dict[str, Any] = {}
    mapping = [
        ("scenario", "scenario"),
        ("status_of_deceased", "status_of_deceased"),
        ("applicant_role", "applicant_role"),
        ("complex_status", "complex_status"),
        ("recipients_count", "recipients_count"),
        ("selected_documents", "selected_documents"),
        ("problem_type", "problem_type"),
        ("submitted_to", "submitted_to"),
        ("months_waiting", "months_waiting"),
        ("region", "region"),
        ("base_total", "base_total"),
        ("personal_share", "personal_share"),
        ("child_monthly_payment_applicable", "child_monthly_payment_applicable"),
        ("estimated_lost_income", "estimated_lost_income"),
        ("lead_name", "lead_name"),
        ("phone", "phone"),
        ("normalized_phone", "normalized_phone"),
        ("contact_method", "contact_method"),
        ("comment", "comment"),
        ("pdn_consent", "pdn_consent"),
    ]
    for src, dst in mapping:
        if src in data and data[src] is not None:
            patch[dst] = data[src]
    if "selected_documents" in data and isinstance(data["selected_documents"], list):
        patch["selected_documents"] = data["selected_documents"]
    return patch


async def sync_progress(repo: LeadRepository, telegram_user_id: int, data: dict[str, Any]) -> None:
    patch = fsm_to_lead_patch(data)
    if patch:
        await repo.update_incomplete(telegram_user_id, patch)


async def sync_progress_with_state(
    repo: LeadRepository,
    telegram_user_id: int,
    *,
    data: dict[str, Any],
    fsm_state: str | None,
) -> None:
    patch = fsm_to_lead_patch(data)
    if fsm_state:
        patch["wizard_state"] = fsm_state
    if patch:
        await repo.update_incomplete(telegram_user_id, patch)


def restore_fsm_from_lead(record: LeadRecord) -> dict[str, Any]:
    """Восстановление словаря для FSM из незавершённого лида (без machine state)."""
    docs = record.selected_documents
    return {
        "scenario": record.scenario,
        "status_of_deceased": record.status_of_deceased,
        "applicant_role": record.applicant_role,
        "complex_status": record.complex_status,
        "recipients_count": record.recipients_count,
        "selected_documents": docs or [],
        "problem_type": record.problem_type,
        "submitted_to": record.submitted_to,
        "months_waiting": record.months_waiting,
        "region": record.region,
        "telegram_user_id": record.telegram_user_id,
        "telegram_username": record.telegram_username,
        "lead_row_id": record.id,
        "base_total": record.base_total,
        "personal_share": record.personal_share,
        "child_monthly_payment_applicable": record.child_monthly_payment_applicable,
        "estimated_lost_income": record.estimated_lost_income,
    }
