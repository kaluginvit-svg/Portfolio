"""CSV import into financial_records and budget_records."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from config import VALID_FINANCIAL_STATEMENT_TYPES, VALID_IMPORT_STATEMENT_TYPES
from db import get_connection
from utils.file_parsers import read_csv_dataframe
from utils.helpers import utc_now_iso

logger = logging.getLogger(__name__)


def _norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.strip().lower()).strip("_")


ALIASES: dict[str, list[str]] = {
    "record_date": [
        "record_date",
        "date",
        "period",
        "month",
        "posting_date",
        "value_date",
        "txn_date",
    ],
    "amount": ["amount", "value", "sum", "total", "amt"],
    "category": ["category", "gl", "account", "line"],
    "subcategory": ["subcategory", "sub_category", "detail"],
    "counterparty": ["counterparty", "vendor", "customer", "partner", "cp"],
    "project": ["project", "proj", "initiative"],
    "department": ["department", "dept", "cost_center"],
    "region": ["region", "geo", "country"],
    "product": ["product", "sku", "sku_name"],
    "currency": ["currency", "ccy", "curr"],
    "company": ["company", "company_name", "entity", "org"],
    "version": ["version", "budget_version", "ver"],
}


def _build_column_map(columns: list[str]) -> dict[str, str]:
    """Map normalized CSV header -> canonical field name."""
    normalized = {_norm_key(c): c for c in columns}
    result: dict[str, str] = {}
    for canonical, variants in ALIASES.items():
        for v in variants:
            nk = _norm_key(v)
            if nk in normalized:
                result[canonical] = normalized[nk]
                break
    return result


def _parse_amount(val: Any) -> float | None:
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(" ", "").replace(",", ".")
    s = re.sub(r"[^\d.\-]", "", s)
    if s in {"", "-", ".", "-."}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date(val: Any) -> str | None:
    if val is None or str(val).strip() == "":
        return None
    s = str(val).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    for fmt in ("%d.%m.%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    try:
        ts = pd.to_datetime(s, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.strftime("%Y-%m-%d")
    except Exception:
        return None


def _resolve_company_id(conn, company_name: str | None, df: pd.DataFrame, col_map: dict[str, str]) -> int:
    if company_name and company_name.strip():
        row = conn.execute(
            "SELECT id FROM companies WHERE name = ? COLLATE NOCASE",
            (company_name.strip(),),
        ).fetchone()
        if not row:
            raise ValueError(f"Company not found: {company_name}")
        return int(row[0])
    if "company" in col_map:
        series = df[col_map["company"]].astype(str).str.strip()
        names = series[series != ""].unique().tolist()
        if len(names) != 1:
            raise ValueError("company_name is required when CSV has zero or multiple distinct company values")
        row = conn.execute(
            "SELECT id FROM companies WHERE name = ? COLLATE NOCASE",
            (names[0],),
        ).fetchone()
        if not row:
            raise ValueError(f"Company not found from CSV: {names[0]}")
        return int(row[0])
    raise ValueError("company_name is required when no company column is present in CSV")


def import_csv(
    file_path: str,
    statement_type: str,
    company_name: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    st = statement_type.strip().lower()
    if st not in VALID_IMPORT_STATEMENT_TYPES:
        return {
            "imported_count": 0,
            "rejected_count": 0,
            "errors": [f"Invalid statement_type: {statement_type}"],
        }

    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        return {"imported_count": 0, "rejected_count": 0, "errors": [f"File not found: {path}"]}

    try:
        df = read_csv_dataframe(path)
    except Exception as e:
        logger.exception("CSV read failed")
        return {"imported_count": 0, "rejected_count": 0, "errors": [f"CSV read error: {e}"]}

    if df.empty:
        return {"imported_count": 0, "rejected_count": 0, "errors": ["CSV has no rows"]}

    col_map = _build_column_map(list(df.columns))
    errors: list[str] = []
    if "record_date" not in col_map:
        errors.append("Missing date column (expected date/record_date/period/...)")
    if "amount" not in col_map:
        errors.append("Missing amount column")
    if errors:
        return {"imported_count": 0, "rejected_count": 0, "errors": errors}

    imported = 0
    rejected = 0
    created = utc_now_iso()
    src = str(path)

    with get_connection() as conn:
        try:
            company_id = _resolve_company_id(conn, company_name, df, col_map)
        except ValueError as e:
            return {"imported_count": 0, "rejected_count": 0, "errors": [str(e)]}

        if st == "budget":
            ver = version or "imported"
            for idx, row in df.iterrows():
                rd = _parse_date(row[col_map["record_date"]])
                amt = _parse_amount(row[col_map["amount"]])
                if rd is None or amt is None:
                    rejected += 1
                    errors.append(f"Row {idx + 2}: invalid date or amount")
                    continue
                cat = str(row[col_map["category"]]).strip() if "category" in col_map else None
                sub = str(row[col_map["subcategory"]]).strip() if "subcategory" in col_map else None
                proj = str(row[col_map["project"]]).strip() if "project" in col_map else None
                dept = str(row[col_map["department"]]).strip() if "department" in col_map else None
                reg = str(row[col_map["region"]]).strip() if "region" in col_map else None
                prod = str(row[col_map["product"]]).strip() if "product" in col_map else None
                ccy = str(row[col_map["currency"]]).strip() if "currency" in col_map else None
                conn.execute(
                    """INSERT INTO budget_records
                    (company_id, record_date, statement_type, category, subcategory, project, department, region, product,
                     amount, currency, version, source_file, created_at)
                    VALUES (?, ?, 'budget', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (company_id, rd, cat or None, sub or None, proj or None, dept or None, reg or None, prod or None, amt, ccy, ver, src, created),
                )
                imported += 1
            conn.commit()
            return {"imported_count": imported, "rejected_count": rejected, "errors": errors[:50]}

        if st not in VALID_FINANCIAL_STATEMENT_TYPES:
            return {"imported_count": 0, "rejected_count": 0, "errors": ["Invalid financial statement_type"]}

        for idx, row in df.iterrows():
            rd = _parse_date(row[col_map["record_date"]])
            amt = _parse_amount(row[col_map["amount"]])
            if rd is None or amt is None:
                rejected += 1
                errors.append(f"Row {idx + 2}: invalid date or amount")
                continue
            cat = str(row[col_map["category"]]).strip() if "category" in col_map else None
            sub = str(row[col_map["subcategory"]]).strip() if "subcategory" in col_map else None
            cp = str(row[col_map["counterparty"]]).strip() if "counterparty" in col_map else None
            proj = str(row[col_map["project"]]).strip() if "project" in col_map else None
            dept = str(row[col_map["department"]]).strip() if "department" in col_map else None
            reg = str(row[col_map["region"]]).strip() if "region" in col_map else None
            prod = str(row[col_map["product"]]).strip() if "product" in col_map else None
            ccy = str(row[col_map["currency"]]).strip() if "currency" in col_map else None
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, subcategory, counterparty, project, department, region, product,
                 amount, currency, source_file, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (company_id, rd, st, cat or None, sub or None, cp or None, proj or None, dept or None, reg or None, prod or None, amt, ccy, src, created),
            )
            imported += 1
        conn.commit()

    return {"imported_count": imported, "rejected_count": rejected, "errors": errors[:50]}
