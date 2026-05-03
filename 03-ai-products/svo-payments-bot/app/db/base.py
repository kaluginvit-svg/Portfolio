"""Инициализация схемы SQLite."""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from app.db.session import aconnect

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS fsm_storage (
    key TEXT PRIMARY KEY,
    state TEXT,
    data TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL,
    telegram_username TEXT,
    telegram_first_name TEXT,
    scenario TEXT,
    status_of_deceased TEXT,
    applicant_role TEXT,
    complex_status TEXT,
    recipients_count INTEGER,
    selected_documents TEXT,
    problem_type TEXT,
    submitted_to TEXT,
    months_waiting INTEGER,
    region TEXT,
    base_total REAL,
    personal_share REAL,
    child_monthly_payment_applicable INTEGER,
    estimated_lost_income REAL,
    lead_name TEXT,
    phone TEXT,
    normalized_phone TEXT,
    contact_method TEXT,
    comment TEXT,
    pdn_consent INTEGER NOT NULL DEFAULT 0,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    wizard_state TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_tg_completed ON leads(telegram_user_id, completed);
"""


async def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aconnect(db_path) as conn:
        await conn.executescript(SCHEMA)
        await conn.commit()
    log.info("База данных готова: %s", db_path)
