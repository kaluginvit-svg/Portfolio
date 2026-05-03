"""Модель записи лида (отражение строки в БД)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LeadRecord:
    id: int | None
    telegram_user_id: int
    telegram_username: str | None
    telegram_first_name: str | None
    scenario: str | None
    status_of_deceased: str | None
    applicant_role: str | None
    complex_status: str | None
    recipients_count: int | None
    selected_documents: list[str] | None
    problem_type: str | None
    submitted_to: str | None
    months_waiting: int | None
    region: str | None
    base_total: float | None
    personal_share: float | None
    child_monthly_payment_applicable: bool | None
    estimated_lost_income: float | None
    lead_name: str | None
    phone: str | None
    normalized_phone: str | None
    contact_method: str | None
    comment: str | None
    pdn_consent: bool
    completed: bool
    created_at: str | None
    updated_at: str | None
    completed_at: str | None
    wizard_state: str | None

    @staticmethod
    def from_row(row: Any) -> LeadRecord:
        import json

        docs_raw = row["selected_documents"]
        docs: list[str] | None
        if docs_raw is None or docs_raw == "":
            docs = None
        else:
            try:
                docs = list(json.loads(docs_raw))
            except json.JSONDecodeError:
                docs = None
        return LeadRecord(
            id=int(row["id"]) if row["id"] is not None else None,
            telegram_user_id=int(row["telegram_user_id"]),
            telegram_username=row["telegram_username"],
            telegram_first_name=row["telegram_first_name"],
            scenario=row["scenario"],
            status_of_deceased=row["status_of_deceased"],
            applicant_role=row["applicant_role"],
            complex_status=row["complex_status"],
            recipients_count=int(row["recipients_count"]) if row["recipients_count"] is not None else None,
            selected_documents=docs,
            problem_type=row["problem_type"],
            submitted_to=row["submitted_to"],
            months_waiting=int(row["months_waiting"]) if row["months_waiting"] is not None else None,
            region=row["region"],
            base_total=float(row["base_total"]) if row["base_total"] is not None else None,
            personal_share=float(row["personal_share"]) if row["personal_share"] is not None else None,
            child_monthly_payment_applicable=bool(row["child_monthly_payment_applicable"])
            if row["child_monthly_payment_applicable"] is not None
            else None,
            estimated_lost_income=float(row["estimated_lost_income"])
            if row["estimated_lost_income"] is not None
            else None,
            lead_name=row["lead_name"],
            phone=row["phone"],
            normalized_phone=row["normalized_phone"],
            contact_method=row["contact_method"],
            comment=row["comment"],
            pdn_consent=bool(row["pdn_consent"]),
            completed=bool(row["completed"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
            wizard_state=row["wizard_state"],
        )
