"""SQLite connection, schema creation, and lifecycle."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterable

from config import DB_PATH

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    currency TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    record_date TEXT NOT NULL,
    statement_type TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    counterparty TEXT,
    project TEXT,
    department TEXT,
    region TEXT,
    product TEXT,
    amount REAL NOT NULL,
    currency TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS budget_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    record_date TEXT NOT NULL,
    statement_type TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    project TEXT,
    department TEXT,
    region TEXT,
    product TEXT,
    amount REAL NOT NULL,
    currency TEXT,
    version TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS cash_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    position_date TEXT NOT NULL,
    bank_account TEXT,
    bank_name TEXT,
    amount REAL NOT NULL,
    currency TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_name TEXT,
    counterparty TEXT,
    start_date TEXT,
    end_date TEXT,
    payment_terms TEXT,
    penalty_terms TEXT,
    currency TEXT,
    amount REAL,
    source_file TEXT,
    raw_text TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS investment_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    company_id INTEGER,
    initial_investment REAL,
    discount_rate REAL,
    hurdle_rate REAL,
    currency TEXT,
    scenario_json TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT,
    severity TEXT,
    message TEXT,
    related_entity TEXT,
    status TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_value TEXT,
    target_type TEXT,
    target_value TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_financial_company_date
    ON financial_records(company_id, record_date);
CREATE INDEX IF NOT EXISTS idx_financial_statement
    ON financial_records(statement_type);
CREATE INDEX IF NOT EXISTS idx_budget_company_version
    ON budget_records(company_id, version);
CREATE INDEX IF NOT EXISTS idx_cash_company_date
    ON cash_positions(company_id, position_date);
"""


def init_database(db_path: Path | None = None) -> Path:
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.info("Database initialized at %s", path)
    finally:
        conn.close()
    return path


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    path = str(Path(db_path or DB_PATH))
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def fetch_all(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, tuple(params))
    return [row_to_dict(r) for r in cur.fetchall()]


def fetch_one(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    cur = conn.execute(sql, tuple(params))
    row = cur.fetchone()
    return row_to_dict(row) if row else None


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    tables = [
        "companies",
        "financial_records",
        "budget_records",
        "cash_positions",
        "contracts",
        "investment_projects",
        "alerts",
        "mappings",
    ]
    out: dict[str, int] = {}
    for t in tables:
        cur = conn.execute(f"SELECT COUNT(*) AS c FROM {t}")
        out[t] = int(cur.fetchone()[0])
    return out
