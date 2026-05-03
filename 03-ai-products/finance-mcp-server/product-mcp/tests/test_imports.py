"""import_csv / import_contract scenarios."""

from __future__ import annotations

import shutil
from pathlib import Path


def _first_company_name(mcp_env) -> str:
    raw = mcp_env.dispatch("list_companies", {})
    assert raw["success"]
    return raw["result"]["companies"][0]["name"]


def test_import_valid_pnl_csv(mcp_env, fixtures_dir: Path):
    company = _first_company_name(mcp_env)
    src = fixtures_dir / "sample_pnl.csv"
    dst = mcp_env.tmp_path / "upload_pnl.csv"
    shutil.copy(src, dst)
    raw = mcp_env.dispatch(
        "import_csv",
        {
            "file_path": str(dst.resolve()),
            "statement_type": "pnl",
            "company_name": company,
        },
    )
    assert raw["success"] is True
    res = raw["result"]
    assert res["imported_count"] > 0
    assert res["rejected_count"] == 0
    listed = mcp_env.dispatch(
        "list_financial_records",
        {"company_name": company, "statement_type": "pnl", "start_date": "2025-03-01"},
    )
    assert listed["success"]
    recs = listed["result"]["records"]
    assert any("upload_pnl" in str(r.get("source_file", "")) or r.get("category") == "Revenue" for r in recs)


def test_import_valid_budget_csv(mcp_env, fixtures_dir: Path):
    company = _first_company_name(mcp_env)
    src = fixtures_dir / "sample_budget.csv"
    dst = mcp_env.tmp_path / "upload_budget.csv"
    shutil.copy(src, dst)
    raw = mcp_env.dispatch(
        "import_csv",
        {
            "file_path": str(dst.resolve()),
            "statement_type": "budget",
            "company_name": company,
            "version": "pytest-v1",
        },
    )
    assert raw["success"] is True
    assert raw["result"]["imported_count"] > 0
    listed = mcp_env.dispatch(
        "list_budget_records",
        {"company_name": company, "version": "pytest-v1"},
    )
    assert listed["success"]
    assert len(listed["result"]["records"]) >= 1


def test_import_payments_csv_for_calendar(mcp_env, fixtures_dir: Path):
    company = _first_company_name(mcp_env)
    src = fixtures_dir / "sample_payments.csv"
    dst = mcp_env.tmp_path / "upload_payments.csv"
    shutil.copy(src, dst)
    raw = mcp_env.dispatch(
        "import_csv",
        {
            "file_path": str(dst.resolve()),
            "statement_type": "payments",
            "company_name": company,
        },
    )
    assert raw["success"] is True
    assert raw["result"]["imported_count"] > 0
    cal = mcp_env.dispatch(
        "payment_calendar",
        {"company_name": company, "start_date": "2025-03-01", "end_date": "2025-03-31"},
    )
    assert cal["success"]
    rows = cal["result"]["records"]
    assert len(rows) >= 1
    assert "direction" in rows[0]
    assert "overdue" in rows[0]


def test_import_invalid_csv_structured_error(mcp_env, fixtures_dir: Path):
    company = _first_company_name(mcp_env)
    src = fixtures_dir / "sample_invalid.csv"
    dst = mcp_env.tmp_path / "bad.csv"
    shutil.copy(src, dst)
    raw = mcp_env.dispatch(
        "import_csv",
        {
            "file_path": str(dst.resolve()),
            "statement_type": "pnl",
            "company_name": company,
        },
    )
    assert raw["success"] is True
    res = raw["result"]
    assert res["imported_count"] == 0
    assert res["rejected_count"] >= 0
    assert any("amount" in e.lower() or "column" in e.lower() for e in res.get("errors", []))


def test_import_contract_txt(mcp_env, fixtures_dir: Path):
    src = fixtures_dir / "sample_contract.txt"
    dst = mcp_env.tmp_path / "contract.txt"
    shutil.copy(src, dst)
    raw = mcp_env.dispatch("import_contract", {"file_path": str(dst.resolve())})
    assert raw["success"] is True
    res = raw["result"]
    assert res.get("contract_id") is not None
    assert res.get("parsed")
    listed = mcp_env.dispatch("list_contracts", {})
    assert listed["success"]
    ids = [c["id"] for c in listed["result"]["records"]]
    assert res["contract_id"] in ids


def test_import_contract_missing_fields_warnings(mcp_env, fixtures_dir: Path):
    src = fixtures_dir / "sample_contract_missing_terms.txt"
    dst = mcp_env.tmp_path / "memo.txt"
    shutil.copy(src, dst)
    raw = mcp_env.dispatch("import_contract", {"file_path": str(dst.resolve())})
    assert raw["success"] is True
    res = raw["result"]
    assert res.get("contract_id") is not None
    warns = res.get("warnings") or []
    assert isinstance(warns, list)
