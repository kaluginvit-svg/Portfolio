"""Проверки расчётного квиза по ТЗ."""

from __future__ import annotations

from app.quizzes.calculate_engine import compute_payment_result


def _base_answers(**kw: str) -> dict[str, str]:
    d = {
        "service_status": "contract_mobilized",
        "applicant_role": "spouse_registered",
        "recipients_count": "2",
        "children_count": "0",
        "death_basis": "duty",
        "ambiguity_flag": "no",
        "region": "Москва",
        "calc_mode": "federal_only",
    }
    d.update(kw)
    return d


def test_children_zero_monthly_zero() -> None:
    r = compute_payment_result(_base_answers(children_count="0"))
    assert r["monthly_children_total"] == 0.0
    assert r["monthly_allowance_part"] == 0.0
    assert r["monthly_pension_part"] == 0.0


def test_recipients_unknown_personal_share_null() -> None:
    r = compute_payment_result(_base_answers(recipients_count="unknown"))
    assert r["personal_share"] is None
    assert r["precision_key"] == "needs_clarification"


def test_cohabitation_always_needs_clarification() -> None:
    r = compute_payment_result(_base_answers(applicant_role="cohabitation_no_marriage"))
    assert r["precision_key"] == "needs_clarification"


def test_volunteer_base_conservative() -> None:
    r = compute_payment_result(
        _base_answers(service_status="volunteer", ambiguity_flag="no", recipients_count="1")
    )
    assert r["lump_sum_total"] == 10_524_892.57
    assert r["consultant_breakdown_insurance_52"] == 0.0


def test_death_unknown_upper_pension_flag() -> None:
    r = compute_payment_result(_base_answers(death_basis="unknown", children_count="1"))
    assert r["needs_clarification_death_basis"] is True
    assert r["precision_key"] == "needs_clarification"
    assert r["monthly_pension_part"] > 0


def test_ambiguity_not_no_needs_clarification() -> None:
    r = compute_payment_result(_base_answers(ambiguity_flag="yes"))
    assert r["precision_key"] == "needs_clarification"
