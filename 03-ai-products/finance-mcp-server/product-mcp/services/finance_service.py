"""Financial queries, KPIs, plan vs fact, search."""

from __future__ import annotations

from typing import Any

from db import fetch_all, get_connection


def resolve_company_id(conn, company_name: str | None) -> int | None:
    if not company_name or not str(company_name).strip():
        return None
    row = conn.execute(
        "SELECT id FROM companies WHERE name = ? COLLATE NOCASE",
        (company_name.strip(),),
    ).fetchone()
    return int(row[0]) if row else None


def require_company_id(conn, company_name: str | None) -> int | None:
    """Return None if no name provided; raise if name provided but unknown."""
    if not company_name or not str(company_name).strip():
        return None
    cid = resolve_company_id(conn, company_name)
    if cid is None:
        raise ValueError(f"Company not found: {company_name}")
    return cid


def opening_cash_balance(conn, company_id: int | None) -> float:
    """Total cash on latest position_date (all companies if company_id is None)."""
    if company_id is None:
        row = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) FROM cash_positions cp
               WHERE (cp.company_id, cp.position_date) IN (
                   SELECT company_id, MAX(position_date) FROM cash_positions GROUP BY company_id
               )"""
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) FROM cash_positions
               WHERE company_id = ? AND position_date = (
                   SELECT MAX(position_date) FROM cash_positions WHERE company_id = ?)""",
            (company_id, company_id),
        ).fetchone()
    return float(row[0])


def _sum_financial_by_statement(
    conn,
    company_id: int | None,
    start: str | None,
    end: str | None,
    statement_type: str,
) -> float:
    sql = "SELECT COALESCE(SUM(amount), 0) FROM financial_records WHERE statement_type = ?"
    params: list[Any] = [statement_type]
    if company_id is not None:
        sql += " AND company_id = ?"
        params.append(company_id)
    if start:
        sql += " AND record_date >= ?"
        params.append(start)
    if end:
        sql += " AND record_date <= ?"
        params.append(end)
    return float(conn.execute(sql, params).fetchone()[0])


def list_companies() -> list[dict[str, Any]]:
    with get_connection() as conn:
        return fetch_all(conn, "SELECT id, name, currency, created_at FROM companies ORDER BY id")


def list_financial_records(
    statement_type: str | None = None,
    company_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
    department: str | None = None,
    project: str | None = None,
    counterparty: str | None = None,
) -> list[dict[str, Any]]:
    sql = """SELECT fr.*, c.name AS company_name
             FROM financial_records fr
             JOIN companies c ON c.id = fr.company_id
             WHERE 1=1"""
    params: list[Any] = []
    with get_connection() as conn:
        cid = require_company_id(conn, company_name)
        if cid is not None:
            sql += " AND fr.company_id = ?"
            params.append(cid)
        if statement_type:
            sql += " AND fr.statement_type = ?"
            params.append(statement_type.strip().lower())
        if start_date:
            sql += " AND fr.record_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND fr.record_date <= ?"
            params.append(end_date)
        if category:
            sql += " AND fr.category LIKE ?"
            params.append(f"%{category}%")
        if department:
            sql += " AND fr.department LIKE ?"
            params.append(f"%{department}%")
        if project:
            sql += " AND fr.project LIKE ?"
            params.append(f"%{project}%")
        if counterparty:
            sql += " AND fr.counterparty LIKE ?"
            params.append(f"%{counterparty}%")
        sql += " ORDER BY fr.record_date, fr.id LIMIT 5000"
        return fetch_all(conn, sql, params)


def list_budget_records(
    company_name: str | None = None,
    version: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    sql = """SELECT br.*, c.name AS company_name
             FROM budget_records br
             JOIN companies c ON c.id = br.company_id
             WHERE 1=1"""
    params: list[Any] = []
    with get_connection() as conn:
        cid = require_company_id(conn, company_name)
        if cid is not None:
            sql += " AND br.company_id = ?"
            params.append(cid)
        if version:
            sql += " AND br.version = ?"
            params.append(version)
        if start_date:
            sql += " AND br.record_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND br.record_date <= ?"
            params.append(end_date)
        if category:
            sql += " AND br.category LIKE ?"
            params.append(f"%{category}%")
        sql += " ORDER BY br.record_date, br.id LIMIT 5000"
        return fetch_all(conn, sql, params)


def _sum_category(conn, company_id: int | None, start: str | None, end: str | None, st: str, category: str) -> float:
    sql = "SELECT COALESCE(SUM(amount), 0) FROM financial_records WHERE statement_type = ? AND category = ?"
    params: list[Any] = [st, category]
    if company_id is not None:
        sql += " AND company_id = ?"
        params.append(company_id)
    if start:
        sql += " AND record_date >= ?"
        params.append(start)
    if end:
        sql += " AND record_date <= ?"
        params.append(end)
    row = conn.execute(sql, params).fetchone()
    return float(row[0])


def calculate_kpis(
    period_start: str | None = None,
    period_end: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    with get_connection() as conn:
        cid = require_company_id(conn, company_name)
        revenue = _sum_category(conn, cid, period_start, period_end, "pnl", "Revenue")
        cogs = _sum_category(conn, cid, period_start, period_end, "pnl", "COGS")
        opex = _sum_category(conn, cid, period_start, period_end, "pnl", "OPEX")
        ebitda_row = _sum_category(conn, cid, period_start, period_end, "pnl", "EBITDA")
        gross_profit = revenue + cogs
        ebitda = ebitda_row if ebitda_row != 0 else revenue + cogs + opex
        margin = (ebitda / revenue) if revenue else None

        net_cash_flow = _sum_financial_by_statement(conn, cid, period_start, period_end, "cashflow")
        ar_total = _sum_financial_by_statement(conn, cid, period_start, period_end, "ar")
        ap_total = _sum_financial_by_statement(conn, cid, period_start, period_end, "ap")
        cash_bal = opening_cash_balance(conn, cid)

    return {
        "total_revenue": revenue,
        "total_opex": abs(opex) if opex < 0 else opex,
        "gross_profit": gross_profit,
        "ebitda": ebitda,
        "ebitda_margin": margin,
        "net_cash_flow": net_cash_flow,
        "accounts_receivable_total": ar_total,
        "accounts_payable_total": abs(ap_total),
        "cash_balance": cash_bal,
    }


def plan_vs_fact(
    period_start: str | None = None,
    period_end: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    with get_connection() as conn:
        cid = require_company_id(conn, company_name)
        bsql = "SELECT category, COALESCE(SUM(amount), 0) AS s FROM budget_records WHERE statement_type = 'budget'"
        fsql = "SELECT category, COALESCE(SUM(amount), 0) AS s FROM financial_records WHERE statement_type = 'pnl' AND category IS NOT NULL"
        bp: list[Any] = []
        fp: list[Any] = []
        if cid is not None:
            bsql += " AND company_id = ?"
            fsql += " AND company_id = ?"
            bp.append(cid)
            fp.append(cid)
        if period_start:
            bsql += " AND record_date >= ?"
            fsql += " AND record_date >= ?"
            bp.append(period_start)
            fp.append(period_start)
        if period_end:
            bsql += " AND record_date <= ?"
            fsql += " AND record_date <= ?"
            bp.append(period_end)
            fp.append(period_end)
        bsql += " GROUP BY category"
        fsql += " GROUP BY category"
        budgets = {r["category"]: float(r["s"]) for r in fetch_all(conn, bsql, bp)}
        facts = {r["category"]: float(r["s"]) for r in fetch_all(conn, fsql, fp)}
        categories = sorted(set(budgets) | set(facts))
        breakdown: list[dict[str, Any]] = []
        total_plan = 0.0
        total_fact = 0.0
        for cat in categories:
            p = budgets.get(cat, 0.0)
            f = facts.get(cat, 0.0)
            total_plan += p
            total_fact += f
            breakdown.append(
                {
                    "category": cat,
                    "plan": p,
                    "fact": f,
                    "variance_abs": f - p,
                    "variance_pct": ((f - p) / p * 100) if p else None,
                }
            )
        var_abs = total_fact - total_plan
        var_pct = (var_abs / total_plan * 100) if total_plan else None
        return {
            "total_plan": total_plan,
            "total_fact": total_fact,
            "variance_abs": var_abs,
            "variance_pct": var_pct,
            "breakdown_by_category": breakdown,
        }


def find_records(query: str) -> list[dict[str, Any]]:
    q = f"%{query.strip()}%"
    out: list[dict[str, Any]] = []
    with get_connection() as conn:
        fr = fetch_all(
            conn,
            """SELECT fr.*, c.name AS company_name, 'financial_record' AS match_type
               FROM financial_records fr
               JOIN companies c ON c.id = fr.company_id
               WHERE fr.category LIKE ? OR fr.subcategory LIKE ? OR fr.counterparty LIKE ?
                  OR fr.project LIKE ? OR fr.source_file LIKE ?""",
            (q, q, q, q, q),
        )
        out.extend(fr)
        cr = fetch_all(
            conn,
            """SELECT *, 'contract' AS match_type FROM contracts
               WHERE contract_name LIKE ? OR counterparty LIKE ? OR source_file LIKE ? OR raw_text LIKE ?""",
            (q, q, q, q),
        )
        out.extend(cr)
    return out[:500]
