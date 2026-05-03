"""Investment project add + evaluate."""

from __future__ import annotations

import json


def _company(mcp_env) -> str:
    r = mcp_env.dispatch("list_companies", {})
    assert r["success"]
    return r["result"]["companies"][0]["name"]


def test_evaluate_investment_seed_project(mcp_env):
    raw = mcp_env.dispatch("evaluate_investment", {"project_id": 1})
    assert raw["success"] is True
    ev = raw["result"]
    assert ev["project_id"] == 1
    for key in ("npv", "irr", "payback_period", "profitability_index", "recommendation"):
        assert key in ev
    assert isinstance(ev["recommendation"], str)
    assert ev["npv"] is not None or ev["recommendation"]


def test_add_investment_project_then_list(mcp_env):
    company = _company(mcp_env)
    scenario = json.dumps({"cash_flows": [100_000, 100_000, 100_000]})
    raw = mcp_env.dispatch(
        "add_investment_project",
        {
            "project_name": "Pytest Capex Line",
            "company_name": company,
            "initial_investment": 200_000,
            "discount_rate": 9.0,
            "hurdle_rate": 10.0,
            "scenario_json": scenario,
            "notes": "pytest",
        },
    )
    assert raw["success"] is True
    res = raw["result"]
    assert res.get("id") is not None
    new_id = res["id"]
    listed = mcp_env.dispatch("list_investment_projects", {})
    assert listed["success"]
    ids = [p["id"] for p in listed["result"]["records"]]
    assert new_id in ids
