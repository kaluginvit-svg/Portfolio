"""Создаёт таблицу users, если её ещё нет (удобно для Docker и первого запуска)."""
import os
import sqlite3
from pathlib import Path

SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tags TEXT NOT NULL
);
"""


def main() -> None:
    db_path = os.environ.get("DB_PATH", "users.db")
    pw_path = Path(os.environ.get("PASSWORDS_FILE", "passwords.txt"))

    Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)
    pw_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SQL)
        conn.commit()
    finally:
        conn.close()

    print(f"init_db: OK ({db_path})")


if __name__ == "__main__":
    main()
