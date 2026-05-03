"""
Подсчёт строк в таблице announcements во всех .db в корне каталога.

Запуск: python count_db_rows.py
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def main() -> None:
    db_files = sorted(BASE_DIR.glob("*.db"))
    db_files = [f for f in db_files if f.is_file()]
    if not db_files:
        print("В каталоге нет файлов .db")
        return

    total_rows = 0
    print("Файл .db                    | строк")
    print("-" * 36)
    for path in db_files:
        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM announcements")
            n = cur.fetchone()[0]
            conn.close()
            total_rows += n
            print(f"  {path.name:<26} | {n}")
        except Exception as e:
            print(f"  {path.name:<26} | ошибка: {e}")
    print("-" * 36)
    print(f"  {'ВСЕГО':<26} | {total_rows}")


if __name__ == "__main__":
    main()
