"""Investment project CRUD and evaluation (NPV, IRR, payback, PI)."""

from __future__ import annotations

import json
import logging
import math
from typing import Any

from db import fetch_all, fetch_one, get_connection
from services.finance_service import resolve_company_id
from utils.helpers import utc_now_iso

logger = logging.getLogger(__name__)


def list_investment_projects() -> list[dict[str, Any]]:
    sql = """SELECT ip.*, c.name AS company_name
             FROM investment_projects ip
             LEFT JOIN companies c ON c.id = ip.company_id
             ORDER BY ip.id"""
    with get_connection() as conn:
        return fetch_all(conn, sql)


def _npv(rate: float, initial: float, flows: list[float]) -> float:
    r = rate / 100.0
    total = -initial
    for t, cf in enumerate(flows, start=1):
        total += cf / ((1.0 + r) ** t)
    return total


def _irr_binary_search(initial: float, flows: list[float], low: float = -0.9999, high: float = 5.0, steps: int = 200) -> float | None:
    """IRR as rate r where NPV(r)=0, rates in decimal form for formula."""

    def npv_dec(r_dec: float) -> float:
        s = -initial
        for t, cf in enumerate(flows, start=1):
            s += cf / ((1.0 + r_dec) ** t)
        return s

    lo_d = low
    hi_d = high
    v_lo = npv_dec(lo_d)
    v_hi = npv_dec(hi_d)
    if math.isnan(v_lo) or math.isnan(v_hi):
        return None
    if v_lo * v_hi > 0:
        return None
    for _ in range(steps):
        mid = (lo_d + hi_d) / 2.0
        v_mid = npv_dec(mid)
        if abs(v_mid) < 1e-6:
            return mid * 100.0
        if v_lo * v_mid <= 0:
            hi_d = mid
            v_hi = v_mid
        else:
            lo_d = mid
            v_lo = v_mid
    return ((lo_d + hi_d) / 2) * 100.0


def _payback_period(initial: float, flows: list[float]) -> float | None:
    if initial <= 0:
        return None
    cum = 0.0
    prev = 0.0
    for t, cf in enumerate(flows, start=1):
        prev = cum
        cum += cf
        if cum >= initial:
            if cf == 0:
                return float(t)
            frac = (initial - prev) / cf
            return (t - 1) + frac
    return None


def _profitability_index(discount_rate: float, initial: float, flows: list[float]) -> float | None:
    if initial <= 0:
        return None
    r = discount_rate / 100.0
    pv = 0.0
    for t, cf in enumerate(flows, start=1):
        pv += cf / ((1.0 + r) ** t)
    return pv / initial


def evaluate_investment(project_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        row = fetch_one(conn, "SELECT * FROM investment_projects WHERE id = ?", (project_id,))
    if not row:
        return {
            "project_id": project_id,
            "npv": None,
            "irr": None,
            "payback_period": None,
            "profitability_index": None,
            "recommendation": "Project not found",
        }

    initial = float(row["initial_investment"] or 0)
    disc = float(row["discount_rate"] or 0)
    hurdle = float(row["hurdle_rate"] or 0)
    flows: list[float] = []
    raw = row.get("scenario_json") or "{}"
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "cash_flows" in data:
            flows = [float(x) for x in data["cash_flows"]]
        elif isinstance(data, list):
            flows = [float(x) for x in data]
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning("Invalid scenario_json for project %s: %s", project_id, e)

    npv_val = _npv(disc, initial, flows) if initial > 0 and flows else None
    irr_val = _irr_binary_search(initial, flows) if initial > 0 and flows else None
    payback = _payback_period(initial, flows) if initial > 0 and flows else None
    pi_val = _profitability_index(disc, initial, flows) if initial > 0 and flows else None

    rec_parts: list[str] = []
    if npv_val is not None:
        rec_parts.append("positive NPV" if npv_val > 0 else "negative NPV")
    if irr_val is not None and hurdle:
        rec_parts.append("IRR above hurdle" if irr_val >= hurdle else "IRR below hurdle")
    if pi_val is not None:
        rec_parts.append("PI>1" if pi_val > 1 else "PI<=1")
    recommendation = "; ".join(rec_parts) if rec_parts else "Insufficient cash flow data"

    return {
        "project_id": project_id,
        "npv": npv_val,
        "irr": irr_val,
        "payback_period": payback,
        "profitability_index": pi_val,
        "recommendation": recommendation,
    }


def add_investment_project(
    project_name: str,
    company_name: str,
    initial_investment: float,
    discount_rate: float,
    hurdle_rate: float,
    scenario_json: str,
    notes: str | None = None,
) -> dict[str, Any]:
    with get_connection() as conn:
        cid = resolve_company_id(conn, company_name)
        if cid is None:
            raise ValueError(f"Company not found: {company_name}")
        created = utc_now_iso()
        cur = conn.execute(
            """INSERT INTO investment_projects
            (project_name, company_id, initial_investment, discount_rate, hurdle_rate, currency, scenario_json, notes, created_at)
            SELECT ?, ?, ?, ?, ?, c.currency, ?, ?, ?
            FROM companies c WHERE c.id = ?""",
            (project_name, cid, initial_investment, discount_rate, hurdle_rate, scenario_json, notes, created, cid),
        )
        conn.commit()
        new_id = int(cur.lastrowid)
    return {"id": new_id, "project_name": project_name, "company_id": cid}
