"""Contract import, listing, and risk scanning."""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from db import fetch_all, get_connection
from utils.file_parsers import read_contract_document
from utils.helpers import utc_now_iso

logger = logging.getLogger(__name__)


_DATE_RE = re.compile(r"\b(20\d{2}|19\d{2})-\d{2}-\d{2}\b")
_MONEY_RE = re.compile(r"\b(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(EUR|USD|GBP)?\b", re.I)
_PENALTY_WORDS = re.compile(r"\b(penalty|late fee|interest|liquidated damages|штраф|неустойк)\b", re.I)


def parse_contract_fields(text: str) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    parsed: dict[str, Any] = {}
    if not text.strip():
        warnings.append("empty_text")
        return parsed, warnings

    iso_dates = list(_DATE_RE.finditer(text))
    if iso_dates:
        parsed["start_date"] = iso_dates[0].group(0)
        if len(iso_dates) > 1:
            parsed["end_date"] = iso_dates[1].group(0)

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines:
        parsed["contract_name"] = lines[0][:200]

    for pat, field in [
        (re.compile(r"(?i)between\s+(.+?)\s+and\s+(.+?)(?:\n|$)"), "counterparty"),
        (re.compile(r"(?i)(vendor|supplier|customer|counterparty)\s*[:#]?\s*(.+)"), "counterparty"),
    ]:
        m = pat.search(text)
        if m:
            parsed["counterparty"] = m.groups()[-1].strip()[:200]
            break

    m2 = _MONEY_RE.search(text)
    if m2:
        raw = m2.group(1).replace(" ", "").replace(",", "")
        try:
            parsed["amount"] = float(raw)
        except ValueError:
            warnings.append("amount_parse_failed")
        if m2.group(2):
            parsed["currency"] = m2.group(2).upper()

    if re.search(r"(?i)net\s*\d+", text):
        parsed["payment_terms"] = "Net terms referenced in text"
    if _PENALTY_WORDS.search(text):
        parsed["penalty_terms"] = "Penalty or interest clause referenced"

    return parsed, warnings


def import_contract(file_path: str) -> dict[str, Any]:
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        return {"contract_id": None, "parsed": {}, "warnings": [f"File not found: {path}"]}

    text, w = read_contract_document(path)
    warnings = list(w)
    parsed, pw = parse_contract_fields(text)
    warnings.extend(pw)

    created = utc_now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO contracts
            (contract_name, counterparty, start_date, end_date, payment_terms, penalty_terms, currency, amount, source_file, raw_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                parsed.get("contract_name"),
                parsed.get("counterparty"),
                parsed.get("start_date"),
                parsed.get("end_date"),
                parsed.get("payment_terms"),
                parsed.get("penalty_terms"),
                parsed.get("currency"),
                parsed.get("amount"),
                str(path),
                text[:500_000],
                created,
            ),
        )
        conn.commit()
        cid = int(cur.lastrowid)
    return {"contract_id": cid, "parsed": parsed, "warnings": warnings}


def list_contracts(active_only: bool = False) -> list[dict[str, Any]]:
    today = date.today().isoformat()
    sql = "SELECT * FROM contracts WHERE 1=1"
    params: list[Any] = []
    if active_only:
        sql += """ AND (start_date IS NULL OR start_date <= ?)
                   AND (end_date IS NULL OR end_date >= ?)"""
        params.extend([today, today])
    sql += " ORDER BY id"
    with get_connection() as conn:
        return fetch_all(conn, sql, params)


def contract_risk_scan() -> dict[str, Any]:
    today = date.today()
    soon = (today + timedelta(days=90)).isoformat()
    expiring: list[dict[str, Any]] = []
    miss_pay: list[dict[str, Any]] = []
    miss_pen: list[dict[str, Any]] = []
    miss_amt: list[dict[str, Any]] = []
    no_end: list[dict[str, Any]] = []
    pen_det: list[dict[str, Any]] = []

    with get_connection() as conn:
        rows = fetch_all(conn, "SELECT * FROM contracts")
        for r in rows:
            end = r.get("end_date")
            if end:
                try:
                    if today.isoformat() <= end <= soon:
                        expiring.append(r)
                except Exception:
                    pass
            else:
                no_end.append(r)
            if not r.get("payment_terms"):
                miss_pay.append(r)
            if not r.get("penalty_terms"):
                miss_pen.append(r)
            if r.get("amount") is None:
                miss_amt.append(r)
            raw = r.get("raw_text") or ""
            if _PENALTY_WORDS.search(raw) or (r.get("penalty_terms") and str(r["penalty_terms"]).strip()):
                pen_det.append(r)

        created = utc_now_iso()
        alerts_n = 0

        def add_alert(atype: str, sev: str, msg: str, rel: str) -> None:
            nonlocal alerts_n
            conn.execute(
                """INSERT INTO alerts (alert_type, severity, message, related_entity, status, created_at)
                   VALUES (?, ?, ?, ?, 'open', ?)""",
                (atype, sev, msg, rel, created),
            )
            alerts_n += 1

        for r in expiring:
            add_alert("contract_expiring", "medium", f"Contract expiring soon: {r.get('contract_name')}", f"contract:{r['id']}")
        for r in miss_pay:
            add_alert("contract_missing_payment_terms", "low", f"Missing payment terms: {r.get('contract_name')}", f"contract:{r['id']}")
        for r in miss_pen:
            add_alert("contract_missing_penalty_terms", "low", f"Missing penalty terms: {r.get('contract_name')}", f"contract:{r['id']}")
        for r in miss_amt:
            add_alert("contract_missing_amount", "medium", f"Missing amount: {r.get('contract_name')}", f"contract:{r['id']}")
        for r in no_end:
            add_alert("contract_no_end_date", "low", f"No end date: {r.get('contract_name')}", f"contract:{r['id']}")
        for r in pen_det:
            add_alert("contract_penalty_detected", "info", f"Penalty language present: {r.get('contract_name')}", f"contract:{r['id']}")

        conn.commit()

    return {
        "expiring_soon": expiring,
        "missing_payment_terms": miss_pay,
        "missing_penalty_terms": miss_pen,
        "missing_amount": miss_amt,
        "no_end_date": no_end,
        "penalty_detected": pen_det,
        "alerts_created": alerts_n,
    }
