"""Smoke: DB init, schema, seed, basic tool availability."""

from __future__ import annotations

import sqlite3


def test_database_file_created(mcp_env):
    assert mcp_env.db_path.is_file()


def test_core_tables_exist(mcp_env):
    conn = sqlite3.connect(str(mcp_env.db_path))
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        names = {row[0] for row in cur.fetchall()}
    finally:
        conn.close()
    for t in (
        "companies",
        "financial_records",
        "budget_records",
        "cash_positions",
        "contracts",
        "investment_projects",
        "alerts",
        "mappings",
    ):
        assert t in names


def test_health_check_after_seed(mcp_env):
    raw = mcp_env.dispatch("health_check", {})
    assert raw["success"] is True
    res = raw["result"]
    assert res["server_status"] == "ok"
    assert "db_path" in res and res["db_path"]
    counts = res["counts_by_table"]
    assert counts.get("companies", 0) >= 1
    assert counts.get("financial_records", 0) >= 1
    assert isinstance(res.get("available_tools"), list)
    assert len(res["available_tools"]) >= 10


def test_list_companies_nonempty(mcp_env):
    raw = mcp_env.dispatch("list_companies", {})
    assert raw["success"] is True
    companies = raw["result"]["companies"]
    assert isinstance(companies, list)
    assert len(companies) >= 1
    assert "name" in companies[0]
