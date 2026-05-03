"""Tool registry and schema bundles integrity."""

from __future__ import annotations

import registry
from schemas import tool_bundles

REQUIRED_TOOLS = frozenset(
    {
        "health_check",
        "list_companies",
        "import_csv",
        "import_contract",
        "list_financial_records",
        "list_budget_records",
        "list_cash_positions",
        "list_contracts",
        "calculate_kpis",
        "plan_vs_fact",
        "liquidity_forecast",
        "payment_calendar",
        "contract_risk_scan",
        "add_investment_project",
        "evaluate_investment",
        "export_report",
        "calculate",
        "find_records",
        "list_investment_projects",
    }
)


def test_required_tools_registered(mcp_env):
    names = set(registry.list_tool_names())
    missing = REQUIRED_TOOLS - names
    assert not missing, f"Missing tools: {missing}"


def test_tool_bundles_match_registry(mcp_env):
    bundle_names = {b.name for b in tool_bundles()}
    reg_names = set(registry.list_tool_names())
    assert bundle_names == reg_names, (
        f"Schema bundle / registry mismatch: only in bundles {bundle_names - reg_names}, "
        f"only in registry {reg_names - bundle_names}"
    )


def test_each_bundle_has_schemas(mcp_env):
    for b in tool_bundles():
        assert b.name
        assert b.description
        assert isinstance(b.input_schema, dict)
        assert b.input_schema.get("title") or "properties" in b.input_schema or "$defs" in b.input_schema
        assert isinstance(b.output_schema, dict)


def test_no_duplicate_tool_names_in_bundles(mcp_env):
    names = [b.name for b in tool_bundles()]
    assert len(names) == len(set(names))
