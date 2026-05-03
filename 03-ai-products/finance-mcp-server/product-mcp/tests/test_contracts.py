"""Contracts listing and risk scan."""

from __future__ import annotations

import sqlite3


def test_list_contracts(mcp_env):
    raw = mcp_env.dispatch("list_contracts", {"active_only": False})
    assert raw["success"] is True
    assert len(raw["result"]["records"]) >= 1


def test_list_contracts_active_only(mcp_env):
    raw_all = mcp_env.dispatch("list_contracts", {"active_only": False})
    raw_act = mcp_env.dispatch("list_contracts", {"active_only": True})
    assert raw_all["success"] and raw_act["success"]
    assert len(raw_act["result"]["records"]) <= len(raw_all["result"]["records"])


def test_contract_risk_scan_structure_and_alerts(mcp_env):
    conn = sqlite3.connect(str(mcp_env.db_path))
    try:
        before = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    finally:
        conn.close()

    raw = mcp_env.dispatch("contract_risk_scan", {})
    assert raw["success"] is True
    scan = raw["result"]
    for key in (
        "expiring_soon",
        "missing_payment_terms",
        "missing_penalty_terms",
        "missing_amount",
        "no_end_date",
        "penalty_detected",
        "alerts_created",
    ):
        assert key in scan
    assert isinstance(scan["alerts_created"], int)

    conn = sqlite3.connect(str(mcp_env.db_path))
    try:
        after = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        rows = conn.execute(
            "SELECT alert_type, severity, message, related_entity FROM alerts ORDER BY id DESC LIMIT 5"
        ).fetchall()
    finally:
        conn.close()
    assert after >= before
    assert len(rows) >= 1
    assert rows[0][0] and rows[0][2]
