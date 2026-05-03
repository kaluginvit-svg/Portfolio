"""Small shared helpers and stable MCP ValueError payloads for tools."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    """UTC timestamp for created_at-style fields (shared by services and seed)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug_filename(prefix: str, ext: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", prefix)[:80]
    return Path(f"{safe}_{ts}.{ext}")


# --- MCP tool layers: ValueError → same dict shapes as before (registry contract) ---


def records_value_error(exc: ValueError) -> dict:
    return {"records": [], "error": str(exc)}


def plan_vs_fact_value_error(exc: ValueError) -> dict:
    return {
        "error": str(exc),
        "total_plan": 0,
        "total_fact": 0,
        "variance_abs": 0,
        "variance_pct": None,
        "breakdown_by_category": [],
    }


def liquidity_forecast_value_error(exc: ValueError) -> dict:
    return {
        "error": str(exc),
        "opening_cash": 0,
        "projected_inflows": 0,
        "projected_outflows": 0,
        "ending_cash": 0,
        "daily_projection": [],
        "risk_flags": [],
    }


def export_report_value_error(report_type: str, exc: ValueError) -> dict:
    return {"path": None, "report_type": report_type, "error": str(exc)}
