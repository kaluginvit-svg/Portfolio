"""export_report creates files under exports dir."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _company(mcp_env) -> str:
    r = mcp_env.dispatch("list_companies", {})
    assert r["success"]
    return r["result"]["companies"][0]["name"]


@pytest.mark.parametrize(
    "report_type,extra",
    [
        ("kpis", {}),
        ("plan_vs_fact", {}),
        ("liquidity_forecast", {}),
        ("payment_calendar", {}),
        ("contract_risks", {}),
        ("investment_evaluation", {"project_id": 1}),
    ],
)
def test_export_report_creates_file(mcp_env, report_type, extra):
    company = _company(mcp_env)
    payload = {
        "report_type": report_type,
        "output_format": "json",
        "company_name": company,
        "period_start": "2024-01-01",
        "period_end": "2024-12-31",
        "liquidity_days": 30,
        "payment_start": "2024-06-01",
        "payment_end": "2024-12-31",
    }
    payload.update(extra)
    raw = mcp_env.dispatch("export_report", payload)
    assert raw["success"] is True, raw
    res = raw["result"]
    assert res.get("error") in (None, "")
    path_str = res.get("path")
    assert path_str
    p = Path(path_str)
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    data = json.loads(text)
    assert "report_type" in data or "data" in data


def test_exports_directory_exists(mcp_env):
    assert mcp_env.exports_dir.is_dir()
