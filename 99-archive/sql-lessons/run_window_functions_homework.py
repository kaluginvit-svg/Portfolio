# -*- coding: utf-8 -*-
"""
Домашнее задание: оконные функции в SQL.
Данные: marketing_data.csv
Результат: window_functions_homework_results.txt с SQL и результатами.
"""
import csv
import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) or "."
CSV_PATH = os.path.join(SCRIPT_DIR, "marketing_data.csv")
DB_PATH = os.path.join(SCRIPT_DIR, "window_functions_homework.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "window_functions_homework_results.txt")


def prn(f, *a, **k):
    print(*a, **k, file=f)


def format_table(f, cur, max_rows=30):
    rows = cur.fetchall()
    if not cur.description:
        prn(f, "(нет выборки)")
        return
    cols = [d[0] for d in cur.description]
    lens = [max(len(str(c)), 4) for c in cols]
    for r in rows:
        for i, v in enumerate(r):
            lens[i] = max(lens[i], len(str(v)) if v is not None else 4)
    fmt = "  ".join("%-" + str(l) + "s" for l in lens)
    prn(f, fmt % tuple(cols))
    prn(f, "-" * (sum(lens) + 2 * (len(cols) - 1)))
    for r in rows[:max_rows]:
        prn(f, fmt % tuple(str(x) if x is not None else "" for x in r))
    if len(rows) > max_rows:
        prn(f, "... (показано %d из %d строк)" % (max_rows, len(rows)))
    prn(f, "Всего строк:", len(rows))


def main():
    if os.path.isfile(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Создаём таблицу и загружаем CSV
    cur.execute("""
        CREATE TABLE marketing_data (
            customer_id INTEGER,
            campaign_id INTEGER,
            purchase_amount REAL,
            purchase_date TEXT,
            region TEXT,
            channel TEXT,
            age INTEGER,
            gender TEXT
        );
    """)
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """INSERT INTO marketing_data
                   (customer_id, campaign_id, purchase_amount, purchase_date, region, channel, age, gender)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(row["customer_id"]),
                    int(row["campaign_id"]),
                    float(row["purchase_amount"]),
                    row["purchase_date"],
                    row["region"],
                    row["channel"],
                    int(row["age"]),
                    row["gender"],
                ),
            )
    conn.commit()

    queries = [
        (
            "1. Доля каждой покупки в общей сумме покупок по клиенту (%)",
            """SELECT
    customer_id,
    campaign_id,
    purchase_amount,
    purchase_date,
    SUM(purchase_amount) OVER (PARTITION BY customer_id) AS customer_total,
    ROUND(100.0 * purchase_amount / SUM(purchase_amount) OVER (PARTITION BY customer_id), 2) AS pct_of_customer
FROM marketing_data
ORDER BY customer_id, purchase_amount DESC;""",
        ),
        (
            "2. Ранжирование клиентов по объёму продаж (по убыванию суммы покупок)",
            """WITH customer_totals AS (
    SELECT customer_id, SUM(purchase_amount) AS total_sales
    FROM marketing_data
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_sales,
    RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
FROM customer_totals
ORDER BY sales_rank;""",
        ),
        (
            "3. Ранжирование регионов по объёму продаж",
            """WITH region_totals AS (
    SELECT region, SUM(purchase_amount) AS total_sales
    FROM marketing_data
    GROUP BY region
)
SELECT
    region,
    total_sales,
    RANK() OVER (ORDER BY total_sales DESC) AS region_rank
FROM region_totals
ORDER BY region_rank;""",
        ),
        (
            "4. Доля каждой покупки в общей сумме покупок по каналу (%)",
            """SELECT
    channel,
    customer_id,
    campaign_id,
    purchase_amount,
    SUM(purchase_amount) OVER (PARTITION BY channel) AS channel_total,
    ROUND(100.0 * purchase_amount / SUM(purchase_amount) OVER (PARTITION BY channel), 2) AS pct_of_channel
FROM marketing_data
ORDER BY channel, purchase_amount DESC;""",
        ),
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        prn(out, "ДОМАШНЕЕ ЗАДАНИЕ: ОКОННЫЕ ФУНКЦИИ В SQL")
        prn(out, "Данные: marketing_data.csv")
        prn(out, "")

        for title, sql in queries:
            prn(out, "=" * 60)
            prn(out, title)
            prn(out, "=" * 60)
            prn(out, "SQL:")
            prn(out, sql.strip())
            prn(out, "")
            cur.execute(sql)
            prn(out, "Результат:")
            format_table(out, cur, max_rows=25)
            prn(out, "")

        prn(out, "Готово.")

    conn.close()
    print("Результаты сохранены в", OUTPUT_PATH)


if __name__ == "__main__":
    main()
