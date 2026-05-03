"""Cash positions, liquidity forecast, payment calendar."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from db import fetch_all, get_connection
from services.finance_service import opening_cash_balance, require_company_id
from utils.dates import today_iso


def list_cash_positions(
    company_name: str | None = None,
    position_date: str | None = None,
) -> list[dict[str, Any]]:
    sql = """SELECT cp.*, c.name AS company_name
             FROM cash_positions cp
             JOIN companies c ON c.id = cp.company_id
             WHERE 1=1"""
    params: list[Any] = []
    with get_connection() as conn:
        cid = require_company_id(conn, company_name)
        if cid is not None:
            sql += " AND cp.company_id = ?"
            params.append(cid)
        if position_date:
            sql += " AND cp.position_date = ?"
            params.append(position_date)
        sql += " ORDER BY cp.position_date DESC, cp.id"
        return fetch_all(conn, sql, params)


def liquidity_forecast(days: int = 90, company_name: str | None = None) -> dict[str, Any]:
    days = max(1, min(int(days), 730))
    today = date.today()
    end = today + timedelta(days=days - 1)
    start_str = today.isoformat()
    end_str = end.isoformat()

    risk_flags: list[str] = []
    with get_connection() as conn:
        cid = require_company_id(conn, company_name)
        opening = opening_cash_balance(conn, cid)

        sql = """SELECT record_date, SUM(amount) AS daily_net
                 FROM financial_records
                 WHERE statement_type = 'payments' AND record_date >= ? AND record_date <= ?"""
        params: list[Any] = [start_str, end_str]
        if cid is not None:
            sql += " AND company_id = ?"
            params.append(cid)
        sql += " GROUP BY record_date"
        rows = fetch_all(conn, sql, params)
        by_date = {r["record_date"]: float(r["daily_net"]) for r in rows}

        if not rows:
            risk_flags.append("no_scheduled_payments_in_window_using_historical_cashflow")
            sql2 = """SELECT record_date, SUM(amount) AS daily_net
                      FROM financial_records
                      WHERE statement_type = 'cashflow' AND record_date >= ? AND record_date <= ?"""
            p2: list[Any] = [start_str, end_str]
            if cid is not None:
                sql2 += " AND company_id = ?"
                p2.append(cid)
            sql2 += " GROUP BY record_date"
            hist = fetch_all(conn, sql2, p2)
            if hist:
                avg = sum(float(h["daily_net"]) for h in hist) / max(len(hist), 1)
                for i in range(days):
                    d = (today + timedelta(days=i)).isoformat()
                    by_date[d] = by_date.get(d, 0.0) + avg / max(days, 1)

        daily_projection: list[dict[str, Any]] = []
        running = opening
        total_in = 0.0
        total_out = 0.0
        for i in range(days):
            d = today + timedelta(days=i)
            ds = d.isoformat()
            net = by_date.get(ds, 0.0)
            inflow = net if net > 0 else 0.0
            outflow = -net if net < 0 else 0.0
            total_in += inflow
            total_out += outflow
            running += net
            daily_projection.append(
                {
                    "date": ds,
                    "net_flow": net,
                    "inflow": inflow,
                    "outflow": outflow,
                    "running_cash": running,
                }
            )

        ending = running
        if ending < 0:
            risk_flags.append("negative_projected_cash")
        if ending < opening * 0.5 and opening > 0:
            risk_flags.append("liquidity_drawdown_over_50pct")

    return {
        "opening_cash": opening,
        "projected_inflows": total_in,
        "projected_outflows": total_out,
        "ending_cash": ending,
        "daily_projection": daily_projection,
        "risk_flags": risk_flags,
    }


def payment_calendar(
    start_date: str | None = None,
    end_date: str | None = None,
    company_name: str | None = None,
) -> list[dict[str, Any]]:
    today_s = today_iso()
    sql = """SELECT fr.*, c.name AS company_name
             FROM financial_records fr
             JOIN companies c ON c.id = fr.company_id
             WHERE fr.statement_type = 'payments'"""
    params: list[Any] = []
    with get_connection() as conn:
        cid = require_company_id(conn, company_name)
        if cid is not None:
            sql += " AND fr.company_id = ?"
            params.append(cid)
        if start_date:
            sql += " AND fr.record_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND fr.record_date <= ?"
            params.append(end_date)
        sql += " ORDER BY fr.record_date, fr.id"
        rows = fetch_all(conn, sql, params)

    out: list[dict[str, Any]] = []
    for r in rows:
        amt = float(r["amount"])
        direction = "inflow" if amt > 0 else "outflow"
        rd = r["record_date"]
        overdue = rd < today_s
        item = dict(r)
        item["direction"] = direction
        item["overdue"] = overdue
        out.append(item)
    return out
