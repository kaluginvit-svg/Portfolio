"""
Добавляет в SQLite с таблицей announcements и колонкой extras_json
новую колонку с текстом из полей «Описание» внутри JSON (только значения).

  venv\\Scripts\\python.exe extras_db_add_opisanie.py fetch_bankrot_trades_table_29-04-2026_29-04-2026_extras_only.db

По умолчанию имя колонки — «Описание» (без дублирования JSON в других колонках).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def collect_opisanie_strings(obj) -> list[str]:
    out: list[str] = []

    def rec(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "Описание":
                    if isinstance(v, str) and v.strip():
                        out.append(v.strip())
                    elif isinstance(v, (dict, list)):
                        out.append(json.dumps(v, ensure_ascii=False))
                    elif v is not None:
                        out.append(str(v).strip())
                elif isinstance(v, (dict, list)):
                    rec(v)
        elif isinstance(o, list):
            for it in o:
                if isinstance(it, (dict, list)):
                    rec(it)

    rec(obj)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description='Добавить колонку «Описание» из extras_json.')
    ap.add_argument("db", help="Файл .db (таблица announcements).")
    ap.add_argument(
        "--column",
        default="Описание",
        help='Имя новой колонки (по умолчанию «Описание»).',
    )
    ap.add_argument(
        "--extras-column",
        default="extras_json",
        help="Имя колонки с JSON.",
    )
    args = ap.parse_args()

    db_path = Path(args.db).expanduser().resolve()
    if not db_path.is_file():
        print(f"Не найден файл: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='announcements'"
    )
    if not cur.fetchone():
        print("Нет таблицы announcements.", file=sys.stderr)
        sys.exit(1)

    cur.execute("PRAGMA table_info(announcements)")
    cols = [r[1] for r in cur.fetchall()]
    extras_name = args.extras_column
    target = args.column

    if extras_name not in cols:
        print(f"Нет колонки «{extras_name}». Есть: {cols}", file=sys.stderr)
        sys.exit(1)

    if target in cols:
        print(f"Колонка «{target}» уже есть — перезапись значений из extras_json.")
    else:
        safe = target.replace('"', '""')
        cur.execute(f'ALTER TABLE announcements ADD COLUMN "{safe}" TEXT')

    esc = extras_name.replace('"', '""')
    cur.execute(f'SELECT rowid, "{esc}" FROM announcements')

    updates = []
    for row in cur.fetchall():
        rid = row[0]
        raw = row[1]
        text = ""
        if raw and str(raw).strip():
            try:
                data = json.loads(raw)
                parts = collect_opisanie_strings(data)
                text = "\n\n".join(parts) if parts else ""
            except json.JSONDecodeError:
                text = ""
        updates.append((text, rid))

    safe_col = target.replace('"', '""')
    cur.executemany(
        f'UPDATE announcements SET "{safe_col}" = ? WHERE rowid = ?',
        updates,
    )
    conn.commit()

    nonempty = sum(1 for t, _ in updates if (t or "").strip())
    print(f"Обновлено строк: {len(updates)}")
    print(f"Непустое «{target}»: {nonempty}")
    print(f"Файл: {db_path}")
    conn.close()


if __name__ == "__main__":
    main()
