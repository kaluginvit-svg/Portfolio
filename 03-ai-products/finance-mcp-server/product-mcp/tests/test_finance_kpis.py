"""calculate_kpis shape and numeric sanity."""

from __future__ import annotations


def _company(mcp_env) -> str:
    r = mcp_env.dispatch("list_companies", {})
    assert r["success"]
    return r["result"]["companies"][0]["name"]


def test_calculate_kpis_fields_and_types(mcp_env):
    name = _company(mcp_env)
    raw = mcp_env.dispatch(
        "calculate_kpis",
        {
            "company_name": name,
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
        },
    )
    assert raw["success"] is True
    k = raw["result"]
    assert "error" not in k or k.get("error") is None
    for key in (
        "total_revenue",
        "total_opex",
        "gross_profit",
        "ebitda",
        "net_cash_flow",
        "accounts_receivable_total",
        "accounts_payable_total",
        "cash_balance",
    ):
        assert key in k
        assert isinstance(k[key], (int, float))
    assert "ebitda_margin" in k
    margin = k["ebitda_margin"]
    assert margin is None or isinstance(margin, (int, float))
