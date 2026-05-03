"""Controlled failures — no crashes."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_unknown_tool(mcp_env):
    raw = mcp_env.dispatch("no_such_tool_ever", {})
    assert raw["success"] is False
    assert "error" in raw


def test_import_csv_unknown_statement_type(mcp_env):
    raw = mcp_env.dispatch(
        "import_csv",
        {
            "file_path": str(Path(__file__).resolve()),
            "statement_type": "not_a_real_type",
            "company_name": "x",
        },
    )
    assert raw["success"] is True
    res = raw["result"]
    assert res["imported_count"] == 0
    assert res["errors"]


def test_import_csv_missing_file(mcp_env):
    missing = mcp_env.tmp_path / "does_not_exist_12345.csv"
    raw = mcp_env.dispatch(
        "import_csv",
        {
            "file_path": str(missing.resolve()),
            "statement_type": "pnl",
            "company_name": "Demo",
        },
    )
    assert raw["success"] is True
    assert "not found" in " ".join(raw["result"].get("errors", [])).lower()


def test_list_financial_unknown_company(mcp_env):
    raw = mcp_env.dispatch(
        "list_financial_records",
        {"company_name": "___NoSuchCompany___"},
    )
    assert raw["success"] is True
    assert raw["result"].get("error")
    assert raw["result"]["records"] == []


def test_calculate_kpis_unknown_company(mcp_env):
    raw = mcp_env.dispatch(
        "calculate_kpis",
        {"company_name": "___NoSuchCompany___"},
    )
    assert raw["success"] is True
    assert raw["result"].get("error")


def test_evaluate_investment_missing_project(mcp_env):
    raw = mcp_env.dispatch("evaluate_investment", {"project_id": 999_999})
    assert raw["success"] is True
    ev = raw["result"]
    assert "not found" in ev.get("recommendation", "").lower() or ev.get("npv") is None


def test_export_unknown_report_type(mcp_env):
    raw = mcp_env.dispatch(
        "export_report",
        {"report_type": "totally_unknown_report", "output_format": "json"},
    )
    assert raw["success"] is True
    assert raw["result"].get("error")


def test_export_investment_without_project_id(mcp_env):
    raw = mcp_env.dispatch(
        "export_report",
        {"report_type": "investment_evaluation", "output_format": "json"},
    )
    assert raw["success"] is True
    assert raw["result"].get("error")
