"""liquidity_forecast and payment_calendar."""

from __future__ import annotations


def _company(mcp_env) -> str:
    r = mcp_env.dispatch("list_companies", {})
    assert r["success"]
    return r["result"]["companies"][0]["name"]


def test_liquidity_forecast_shape(mcp_env):
    name = _company(mcp_env)
    raw = mcp_env.dispatch("liquidity_forecast", {"company_name": name, "days": 30})
    assert raw["success"] is True
    L = raw["result"]
    assert "error" not in L or L.get("error") is None
    for key in (
        "opening_cash",
        "projected_inflows",
        "projected_outflows",
        "ending_cash",
        "daily_projection",
        "risk_flags",
    ):
        assert key in L
    assert isinstance(L["daily_projection"], list)
    assert len(L["daily_projection"]) == 30
    assert isinstance(L["risk_flags"], list)


def test_payment_calendar_direction_and_overdue(mcp_env):
    name = _company(mcp_env)
    raw = mcp_env.dispatch(
        "payment_calendar",
        {"company_name": name, "start_date": "2024-06-01", "end_date": "2024-12-31"},
    )
    assert raw["success"] is True
    rows = raw["result"]["records"]
    assert isinstance(rows, list)
    assert len(rows) >= 1
    row = rows[0]
    assert row["direction"] in ("inflow", "outflow")
    assert isinstance(row["overdue"], bool)
