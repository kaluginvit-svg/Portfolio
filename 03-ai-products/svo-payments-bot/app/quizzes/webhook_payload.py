"""Единый JSON payload для webhook после квиза."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.legal_docs import CONSENT_DOC_FILENAME, POLICY_DOC_FILENAME
from app.quizzes.calculate_engine import compute_payment_result
from app.quizzes.clarify_derived import compute_clarify_derived

QUIZ_CLARIFY = "clarify_situation"
QUIZ_CALCULATE = "calculate_payments"

PERSONAL_DATA_CONSENT_TEXT = (
    "Нажимая «Продолжить», пользователь соглашается на обработку персональных данных "
    "в соответствии с политикой и текстом согласия."
)


def build_quiz_webhook_payload(
    *,
    quiz_type: str,
    raw_answers: dict[str, str],
    lead_name: str,
    lead_phone: str,
    personal_data_consent: bool,
    consent_doc_url: str,
    policy_doc_url: str,
) -> dict[str, Any]:
    submitted_at = datetime.now(timezone.utc).isoformat()
    base: dict[str, Any] = {
        "source": "telegram_bot",
        "quiz_type": quiz_type,
        "submitted_at": submitted_at,
        "raw_answers": dict(raw_answers),
        "lead_name": lead_name,
        "lead_phone": lead_phone,
        "personal_data_consent": personal_data_consent,
        "personal_data_consent_text": PERSONAL_DATA_CONSENT_TEXT,
        "personal_data_policy_url": policy_doc_url,
        "personal_data_consent_url": consent_doc_url,
        "personal_data_consent_filename": CONSENT_DOC_FILENAME,
        "personal_data_policy_filename": POLICY_DOC_FILENAME,
    }

    if quiz_type == QUIZ_CLARIFY:
        d = compute_clarify_derived(raw_answers)
        base.update(
            {
                "stage_score": d["stage_score"],
                "stage_label": d["stage_label"],
                "journey_phase": d["journey_phase"],
                "lead_temperature": d["lead_temperature"],
                "death_certificate_status": d["death_certificate_status"],
                "military_notice_status": d["military_notice_status"],
                "kinship_docs_status": d["kinship_docs_status"],
                "submission_pack_status": d["submission_pack_status"],
                "filing_status": d["filing_status"],
                "filing_route": d["filing_route"],
                "current_case_state": d["current_case_state"],
                "primary_blocker": d["primary_blocker"],
                "secondary_blocker_line": d["secondary_blocker_line"],
                "user_focus": d["user_focus"],
                "consultant_summary": d["consultant_summary"],
                "consultant_step_1": d["consultant_step_1"],
                "consultant_step_2": d["consultant_step_2"],
                "consultant_step_3": d["consultant_step_3"],
            }
        )
    elif quiz_type == QUIZ_CALCULATE:
        c = compute_payment_result(raw_answers)
        base.update(
            {
                "service_status": raw_answers.get("service_status"),
                "applicant_role": raw_answers.get("applicant_role"),
                "recipients_count": raw_answers.get("recipients_count"),
                "children_count": raw_answers.get("children_count"),
                "death_basis": raw_answers.get("death_basis"),
                "ambiguity_flag": raw_answers.get("ambiguity_flag"),
                "region": raw_answers.get("region"),
                "calc_mode": raw_answers.get("calc_mode"),
                "consultant_total_amount": c["headline_amount"],
                "consultant_total_amount_label": c["headline_prefix"],
                "consultant_lump_sum_total": c["lump_sum_total"],
                "consultant_personal_share": c["personal_share"],
                "consultant_monthly_children_total": c["monthly_children_total"],
                "consultant_monthly_allowance_part": c["monthly_allowance_part"],
                "consultant_monthly_pension_part": c["monthly_pension_part"],
                "consultant_precision_label": c["precision_label"],
                "consultant_summary": c["consultant_summary"],
                "consultant_breakdown_lump_sum": c["lump_sum_total"],
                "consultant_breakdown_president_payment": c["consultant_breakdown_president_payment"],
                "consultant_breakdown_306_payment": c["consultant_breakdown_306_payment"],
                "consultant_breakdown_insurance_52": c["consultant_breakdown_insurance_52"],
                "consultant_breakdown_monthly_child_allowance": c["consultant_breakdown_monthly_child_allowance"],
                "consultant_breakdown_monthly_child_pension": c["consultant_breakdown_monthly_child_pension"],
                "consultant_breakdown_region_included": c["consultant_breakdown_region_included"],
                "consultant_breakdown_region_note": c["consultant_breakdown_region_note"],
                "radiation_module_status": c["radiation_module_status"],
                "radiation_module_note": c["radiation_module_note"],
            }
        )

    return base
