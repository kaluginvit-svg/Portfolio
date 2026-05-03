# -*- coding: utf-8 -*-
"""SQLite-хранилище для путешествий и расходов."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "travel_wallet.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                active_trip_id INTEGER,
                FOREIGN KEY (active_trip_id) REFERENCES trips(id)
            );
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                from_country TEXT NOT NULL,
                to_country TEXT NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                balance_dest REAL NOT NULL,
                balance_home REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                amount_dest REAL NOT NULL,
                amount_home REAL NOT NULL,
                purpose TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (trip_id) REFERENCES trips(id)
            );
            CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id);
            CREATE INDEX IF NOT EXISTS idx_expenses_trip ON expenses(trip_id);
        """)
        conn.commit()
        # Миграция: добавить колонку purpose в старых БД
        try:
            conn.execute("ALTER TABLE expenses ADD COLUMN purpose TEXT DEFAULT ''")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    finally:
        conn.close()


def ensure_user(user_id: int):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()


def get_active_trip_id(user_id: int) -> int | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT active_trip_id FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return row["active_trip_id"] if row and row["active_trip_id"] else None
    finally:
        conn.close()


def set_active_trip(user_id: int, trip_id: int | None):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET active_trip_id = ? WHERE user_id = ?",
            (trip_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_trip(trip_id: int, user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM trips WHERE id = ? AND user_id = ?",
            (trip_id, user_id),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_trips(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_trip(
    user_id: int,
    from_country: str,
    to_country: str,
    from_currency: str,
    to_currency: str,
    rate: float,
    balance_dest: float,
    balance_home: float,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO trips
               (user_id, from_country, to_country, from_currency, to_currency,
                rate, balance_dest, balance_home)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                from_country,
                to_country,
                from_currency,
                to_currency,
                rate,
                balance_dest,
                balance_home,
            ),
        )
        conn.commit()
        trip_id = cur.lastrowid
        conn.execute(
            "UPDATE users SET active_trip_id = ? WHERE user_id = ?",
            (trip_id, user_id),
        )
        conn.commit()
        return trip_id
    finally:
        conn.close()


def update_trip_rate(trip_id: int, user_id: int, rate: float) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE trips SET rate = ? WHERE id = ? AND user_id = ?",
            (rate, trip_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def add_expense(trip_id: int, user_id: int, amount_dest: float, amount_home: float, purpose: str = ""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO expenses (trip_id, amount_dest, amount_home, purpose) VALUES (?, ?, ?, ?)",
            (trip_id, amount_dest, amount_home, (purpose or "").strip()),
        )
        conn.execute(
            "UPDATE trips SET balance_dest = balance_dest - ?, balance_home = balance_home - ? WHERE id = ? AND user_id = ?",
            (amount_dest, amount_home, trip_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_expenses(trip_id: int, user_id: int, limit: int = 50) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT e.* FROM expenses e
               JOIN trips t ON e.trip_id = t.id
               WHERE e.trip_id = ? AND t.user_id = ?
               ORDER BY e.created_at DESC LIMIT ?""",
            (trip_id, user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_expenses_grouped_by_purpose(trip_id: int, user_id: int) -> list[dict]:
    """Группировка расходов по назначению (purpose). Возвращает список групп с суммами и списком (сумма, дата)."""
    expenses = get_expenses(trip_id, user_id, limit=500)
    groups: dict[str, list[dict]] = {}
    for e in expenses:
        purpose = (e.get("purpose") or "").strip() or "—"
        key = purpose.lower()
        if key not in groups:
            groups[key] = {"purpose": purpose, "items": [], "total_dest": 0, "total_home": 0}
        groups[key]["items"].append({
            "amount_dest": e["amount_dest"],
            "amount_home": e["amount_home"],
            "created_at": e["created_at"],
        })
        groups[key]["total_dest"] += e["amount_dest"]
        groups[key]["total_home"] += e["amount_home"]
    return list(groups.values())


def format_balance(balance_dest: float, balance_home: float, to_cur: str, from_cur: str) -> str:
    return f"{balance_dest:,.2f} {to_cur} = {balance_home:,.2f} {from_cur}".replace(",", " ")


def format_balance_breakdown(grouped: list[dict], to_cur: str, from_cur: str) -> str:
    """Формирует строку «в т.ч.»: по каждой категории — сумма и расшифровка (сколько, когда)."""
    if not grouped:
        return ""
    lines = []
    for g in grouped:
        purpose = g["purpose"]
        total_d = g["total_dest"]
        total_h = g["total_home"]
        n = len(g["items"])
        parts = []
        for it in g["items"]:
            s = (it["created_at"] or "")[:10]
            dt = f"{s[8:10]}.{s[5:7]}" if len(s) >= 10 else s
            parts.append(f"{dt} {it['amount_dest']:.0f}")
        detail = ", ".join(parts)
        if n > 1:
            lines.append(f"  в т.ч. {purpose}: {total_d:,.0f} {to_cur} ({n} раз: {detail})".replace(",", " "))
        else:
            lines.append(f"  в т.ч. {purpose}: {total_d:,.0f} {to_cur} ({detail})".replace(",", " "))
    return "\n".join(lines)
