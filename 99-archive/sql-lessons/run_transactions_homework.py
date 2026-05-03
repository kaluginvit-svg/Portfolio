# -*- coding: utf-8 -*-
"""
Тема: «Фильтрация и сортировка агрегированных данных».
Скрипт загружает transactions (1).csv в SQLite, выполняет задания и выводит результаты в transactions_homework_results.txt.
"""
import sqlite3
import csv
import os

DB_PATH = "transactions_homework.db"
# Имя файла CSV (с пробелом и скобками в имени)
CSV_PATH = "transactions (1).csv"
OUTPUT_PATH = "transactions_homework_results.txt"


def _prn(output, *a, **k):
    """Печать в переданный поток (файл или консоль)."""
    print(*a, **k, file=output)


def _format_table(output, cur):
    """Форматирует результат последнего запроса в виде таблицы и выводит в output."""
    rows = cur.fetchall()
    if not cur.description:
        _prn(output, "Строк: 0")
        return 0
    cols = [d[0] for d in cur.description]
    lens = [max(len(str(c)), 4) for c in cols]
    for r in rows:
        for i, v in enumerate(r):
            lens[i] = max(lens[i], len(str(v)) if v is not None else 4)
    fmt = "  ".join("%-" + str(l) + "s" for l in lens)
    _prn(output, fmt % tuple(cols))
    _prn(output, "-" * (sum(lens) + 2 * (len(cols) - 1)))
    for r in rows:
        _prn(output, fmt % tuple(str(x) if x is not None else "" for x in r))
    _prn(output, "Строк:", len(rows))
    return len(rows)


def main(output=None):
    if output is None:
        output = __import__("sys").stdout

    script_dir = os.path.dirname(os.path.abspath(__file__)) or "."
    csv_path = os.path.join(script_dir, CSV_PATH)

    # Подключение к SQLite и создание таблицы transactions
    conn = sqlite3.connect(os.path.join(script_dir, DB_PATH))
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute("""
        CREATE TABLE transactions (
            account_id INTEGER,
            transaction_date TEXT,
            transaction_amount REAL,
            transaction_type TEXT,
            currency TEXT,
            branch_id INTEGER,
            transaction_status TEXT,
            customer_id INTEGER,
            transaction_fee REAL,
            balance_before REAL,
            balance_after REAL
        )
    """)

    # Загрузка данных из CSV (пустые поля — NULL)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            def num(s, f=float):
                s = (row.get(s) or "").strip()
                return f(s) if s else None
            def int_(s):
                return num(s, int)
            conn.execute(
                """INSERT INTO transactions (
                    account_id, transaction_date, transaction_amount, transaction_type,
                    currency, branch_id, transaction_status, customer_id,
                    transaction_fee, balance_before, balance_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    int_("account_id"),
                    (row.get("transaction_date") or "").strip() or None,
                    num("transaction_amount"),
                    (row.get("transaction_type") or "").strip() or None,
                    (row.get("currency") or "").strip() or None,
                    int_("branch_id"),
                    (row.get("transaction_status") or "").strip() or None,
                    int_("customer_id"),
                    num("transaction_fee"),
                    num("balance_before"),
                    num("balance_after"),
                ),
            )
    conn.commit()
    cur = conn.cursor()

    # Заголовок отчёта и комментарии к решению (из задания)
    _prn(output, "ФИЛЬТРАЦИЯ И СОРТИРОВКА АГРЕГИРОВАННЫХ ДАННЫХ (ТРАНЗАКЦИИ)")
    _prn(output, "Источник данных: transactions (1).csv → таблица transactions.")
    _prn(output, "Поля: account_id, transaction_date, transaction_amount, transaction_type, currency, branch_id, transaction_status, customer_id, ...")
    _prn(output, "")
    _prn(output, "Комментарии к решению (из задания):")
    _prn(output, "• Задача 1: группировка по полю «transaction_status» и функция AVG для поля «transaction_amount».")
    _prn(output, "• Задача 2: группировка по полю «transaction_type» и функция MAX для поля «transaction_amount».")
    _prn(output, "• Задача 5: условная конструкция CASE WHEN для комбинированного статуса.")
    _prn(output, "")

    # Список заданий: (заголовок, комментарий к решению, SQL-запрос)
    tasks = [
        (
            "1. Средний размер транзакции по статусам failed, completed и pending",
            "Группировка по полю transaction_status; функция AVG(transaction_amount) для каждого статуса.",
            "SELECT transaction_status, ROUND(AVG(transaction_amount), 2) AS avg_amount FROM transactions GROUP BY transaction_status ORDER BY transaction_status",
        ),
        (
            "2. Максимальный размер транзакции на пополнение (deposit) и снятие (withdrawal)",
            "Группировка по полю transaction_type; функция MAX(transaction_amount) для каждого типа.",
            "SELECT transaction_type, MAX(transaction_amount) AS max_amount FROM transactions GROUP BY transaction_type ORDER BY transaction_type",
        ),
        (
            "3. Клиенты, у которых максимальная сумма снятия была больше 2000 (в любой валюте)",
            "Фильтр transaction_type = 'withdrawal', группировка по customer_id, HAVING MAX(transaction_amount) > 2000.",
            """SELECT customer_id, MAX(transaction_amount) AS max_withdrawal
FROM transactions
WHERE transaction_type = 'withdrawal'
GROUP BY customer_id
HAVING MAX(transaction_amount) > 2000
ORDER BY max_withdrawal DESC""",
        ),
        (
            "4. Клиенты, которые в среднем вносят на счёт от 1000 до 2000 за транзакцию (USD или EUR)",
            "Фильтр: transaction_type = 'deposit' и currency IN ('USD','EUR'); группировка по customer_id; HAVING AVG(transaction_amount) BETWEEN 1000 AND 2000.",
            """SELECT customer_id, ROUND(AVG(transaction_amount), 2) AS avg_deposit_usd_eur
FROM transactions
WHERE transaction_type = 'deposit' AND currency IN ('USD', 'EUR')
GROUP BY customer_id
HAVING AVG(transaction_amount) BETWEEN 1000 AND 2000
ORDER BY customer_id""",
        ),
        (
            "5. Комбинированный статус transaction_comb_status (CASE WHEN)",
            "Условная конструкция CASE WHEN: withdrawal+failed=1, withdrawal+completed=2, withdrawal+pending=3, deposit+failed=4, deposit+completed=5, deposit+pending=6.",
            """SELECT account_id, transaction_date, transaction_type, transaction_status,
  CASE
    WHEN transaction_type = 'withdrawal' AND transaction_status = 'failed' THEN 1
    WHEN transaction_type = 'withdrawal' AND transaction_status = 'completed' THEN 2
    WHEN transaction_type = 'withdrawal' AND transaction_status = 'pending' THEN 3
    WHEN transaction_type = 'deposit' AND transaction_status = 'failed' THEN 4
    WHEN transaction_type = 'deposit' AND transaction_status = 'completed' THEN 5
    WHEN transaction_type = 'deposit' AND transaction_status = 'pending' THEN 6
    ELSE NULL
  END AS transaction_comb_status
FROM transactions
ORDER BY account_id, transaction_date
LIMIT 100""",
        ),
        (
            "6. Популярность платежного терминала (branch_id) по количеству транзакций в день",
            "Группировка по branch_id и дате (день). Если транзакций в день <= 3 — «Normal», иначе — «Popular» (CASE WHEN по COUNT).",
            """SELECT branch_id, date(transaction_date) AS day, COUNT(*) AS transactions_per_day,
  CASE WHEN COUNT(*) <= 3 THEN 'Normal' ELSE 'Popular' END AS popularity
FROM transactions
GROUP BY branch_id, date(transaction_date)
ORDER BY branch_id, day""",
        ),
    ]

    for title, comment, sql in tasks:
        _prn(output, "\n" + "=" * 60)
        _prn(output, title)
        _prn(output, "=" * 60)
        _prn(output, "Комментарий к решению:", comment)
        _prn(output, "SQL (полный скрипт):")
        _prn(output, sql.strip())
        _prn(output, "")
        cur.execute(sql)
        _format_table(output, cur)

    conn.close()
    _prn(output, "\nГотово.")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__)) or "."
    out_path = os.path.join(script_dir, OUTPUT_PATH)
    with open(out_path, "w", encoding="utf-8") as f:
        main(f)
    print("Результаты сохранены в", out_path)
