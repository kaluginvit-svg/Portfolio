"""plan_vs_fact structure and non-empty breakdown."""

from __future__ import annotations


def _company(mcp_env) -> str:
    r = mcp_env.dispatch("list_companies", {})
    assert r["success"]
    return r["result"]["companies"][0]["name"]


def test_plan_vs_fact_structure(mcp_env):
    name = _company(mcp_env)
    raw = mcp_env.dispatch(
        "plan_vs_fact",
        {
            "company_name": name,
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
        },
    )
    assert raw["success"] is True
    p = raw["result"]
    assert "error" not in p or p.get("error") is None
    for key in ("total_plan", "total_fact", "variance_abs", "variance_pct", "breakdown_by_category"):
        assert key in p
    assert isinstance(p["breakdown_by_category"], list)
    assert len(p["breakdown_by_category"]) >= 1
    row = p["breakdown_by_category"][0]
    assert "category" in row and "plan" in row and "fact" in row
