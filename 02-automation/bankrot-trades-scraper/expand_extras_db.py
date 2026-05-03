"""
Новая БД на основе существующей: раскрыть выбранные поля из JSON в колонку extras_json.

Использование:
  # Только одна колонка extras_json, текст как в исходной БД (без разбора JSON):
  venv\\Scripts\\python.exe expand_extras_db.py вход.db --only-extras

  # Раскрытие частых ключей в отдельные колонки:
  venv\\Scripts\\python.exe expand_extras_db.py вход.db
  venv\\Scripts\\python.exe expand_extras_db.py вход.db --out выход.db --top 100 --min-rows 2
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _sanitize(name: str) -> str:
    s = re.sub(r"[^\w\u0400-\u04ff]", "_", (name or "").strip())
    return s or "col_" + str(abs(hash(name)))[:8]


def _unique_headers(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for i, h in enumerate(names):
        n = _sanitize(h) or f"col_{i}"
        while n in seen:
            n = n + "_" + str(i)
        seen.add(n)
        out.append(n)
    return out


def _flatten_extras(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Вложенные dict → ключи с точками; list → одна строка."""
    out: dict[str, Any] = {}
    if obj is None:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                out.update(_flatten_extras(v, p))
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    parts = []
                    for j, it in enumerate(v[:100]):
                        if isinstance(it, dict):
                            sub = _flatten_extras(it, f"{p}[{j}]")
                            parts.append(json.dumps(sub, ensure_ascii=False))
                        else:
                            parts.append(str(it))
                    out[p] = " | ".join(parts)
                else:
                    out[p] = "; ".join(str(x) for x in v[:200])
            else:
                out[p] = v
    return out


def _cell(v: Any, max_len: int) -> str:
    if v is None:
        return ""
    s = str(v).replace("\x00", "")
    return s if len(s) <= max_len else s[:max_len]


_MAX = 1_000_000


def collect_key_counts(cur: sqlite3.Cursor, extras_col: str) -> Counter[str]:
    cur.execute(f'SELECT "{extras_col}" FROM announcements')
    ctr: Counter[str] = Counter()
    for (raw,) in cur.fetchall():
        if not raw or not str(raw).strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        flat = _flatten_extras(data)
        ctr.update(flat.keys())
    return ctr


def main() -> None:
    ap = argparse.ArgumentParser(description="Раскрыть extras_json в отдельные колонки (новая .db).")
    ap.add_argument("input_db", help="Исходный SQLite (таблица announcements, колонка extras_json).")
    ap.add_argument("--out", metavar="PATH", help="Выходной файл (по умолчанию *_expanded.db).")
    ap.add_argument("--top", type=int, default=80, help="Сколько самых частых ключей вынести в колонки (по умолчанию 80).")
    ap.add_argument(
        "--min-rows",
        type=int,
        default=1,
        help="Минимум строк, где ключ должен встретиться, чтобы попасть в топ (по умолчанию 1).",
    )
    ap.add_argument(
        "--extras-column",
        default="extras_json",
        help="Имя колонки с JSON (по умолчанию extras_json).",
    )
    ap.add_argument("--prefix", default="ex_", help="Префикс имён новых колонок из extras (по умолчанию ex_).")
    ap.add_argument(
        "--only-extras",
        action="store_true",
        help="Выходная БД: только таблица announcements с одной колонкой extras_json (значение как в исходнике).",
    )
    args = ap.parse_args()

    src = Path(args.input_db).expanduser().resolve()
    if not src.is_file():
        print(f"Файл не найден: {src}", file=sys.stderr)
        sys.exit(1)

    if args.only_extras:
        out_default = src.with_name(src.stem + "_extras_only.db")
    else:
        out_default = src.with_name(src.stem + "_expanded.db")
    out_path = Path(args.out).expanduser().resolve() if args.out else out_default

    conn = sqlite3.connect(str(src))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='announcements'")
    if not cur.fetchone():
        print("В БД нет таблицы announcements.", file=sys.stderr)
        sys.exit(1)

    cur.execute("PRAGMA table_info(announcements)")
    cols_info = cur.fetchall()
    col_names = [r[1] for r in cols_info]
    extras_name = args.extras_column
    if extras_name not in col_names:
        print(f"Нет колонки «{extras_name}». Есть: {col_names[:30]}...", file=sys.stderr)
        sys.exit(1)

    if args.only_extras:
        out_conn = sqlite3.connect(str(out_path))
        out_conn.execute("PRAGMA encoding = 'UTF-8'")
        oc = out_conn.cursor()
        oc.execute("DROP TABLE IF EXISTS announcements")
        oc.execute('CREATE TABLE announcements ("extras_json" TEXT)')
        q = f'SELECT "{extras_name}" FROM announcements'
        batch = [(r[0],) for r in cur.execute(q)]
        oc.executemany("INSERT INTO announcements (extras_json) VALUES (?)", batch)
        out_conn.commit()
        out_conn.close()
        conn.close()
        print(f"Строк: {len(batch)}")
        print(f"Только колонка extras_json (как в исходной БД): {out_path}")
        return

    ctr = collect_key_counts(cur, extras_name)
    if not ctr:
        print("extras_json пуст или не парсится — копируем таблицу без раскрытия отдельных полей.")
        selected = []
    else:
        ranked = [k for k, n in ctr.most_common() if n >= args.min_rows]
        selected = ranked[: max(0, args.top)]

    base_cols = [c for c in col_names if c != extras_name]
    new_names = [args.prefix + _sanitize(k) for k in selected]
    new_names = _unique_headers(new_names)
    # карта выбранный_ключ -> имя_колонки
    key_to_col = dict(zip(selected, new_names))

    out_conn = sqlite3.connect(str(out_path))
    out_cur = out_conn.cursor()
    out_conn.execute("PRAGMA encoding = 'UTF-8'")

    all_out_cols = base_cols + list(new_names) + ["extras_leftover"]
    defs = ", ".join(f'"{c}" TEXT' for c in all_out_cols)
    out_cur.execute(f"DROP TABLE IF EXISTS announcements")
    out_cur.execute(f"CREATE TABLE announcements ({defs})")

    cur.execute(f'SELECT * FROM announcements')
    placeholders = ", ".join("?" * len(all_out_cols))
    quoted = ", ".join(f'"{c}"' for c in all_out_cols)
    insert_sql = f'INSERT INTO announcements ({quoted}) VALUES ({placeholders})'

    n_rows = 0
    for row in cur.execute(f'SELECT * FROM announcements'):
        d = dict(row)
        raw_extras = d.get(extras_name)
        leftover: dict[str, Any] = {}
        ex_vals: dict[str, str] = {c: "" for c in new_names}

        if raw_extras and str(raw_extras).strip():
            try:
                data = json.loads(raw_extras)
                flat = _flatten_extras(data) if isinstance(data, dict) else {}
                for k, v in flat.items():
                    if k in key_to_col:
                        col = key_to_col[k]
                        ex_vals[col] = _cell(v, _MAX)
                    else:
                        leftover[k] = v
            except json.JSONDecodeError:
                leftover["_raw_extras_parse_error"] = str(raw_extras)[:10_000]

        row_out: list[str] = []
        for c in base_cols:
            row_out.append(_cell(d.get(c), _MAX))
        for c in new_names:
            row_out.append(ex_vals.get(c, ""))
        row_out.append(_cell(json.dumps(leftover, ensure_ascii=False), _MAX) if leftover else "")

        out_cur.execute(insert_sql, row_out)
        n_rows += 1

    out_conn.commit()
    out_conn.close()
    conn.close()

    meta = {
        "source": str(src),
        "output": str(out_path),
        "rows": n_rows,
        "extras_keys_total_unique": len(ctr),
        "columns_from_extras": selected,
        "column_mapping": key_to_col,
    }
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Записано строк: {n_rows}")
    print(f"Выходная БД: {out_path}")
    print(f"Вынесено колонок из extras: {len(selected)} (топ по частоте)")
    print(f"Описание колонок и ключей: {meta_path}")


if __name__ == "__main__":
    main()
