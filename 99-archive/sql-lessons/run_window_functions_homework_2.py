# -*- coding: utf-8 -*-
"""
Домашнее задание: функции ранжирования и смещения (оконные функции).
NTILE, LEAD, LAG, FIRST_VALUE, LAST_VALUE.
Данные: marketing_data.csv
Результат: window_functions_homework_2_results.txt
"""
import csv
import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) or "."
CSV_PATH = os.path.join(SCRIPT_DIR, "marketing_data.csv")
DB_PATH = os.path.join(SCRIPT_DIR, "window_functions_homework_2.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "window_functions_homework_2_results.txt")


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


def load_data(cur):
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


def main():
    if os.path.isfile(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    load_data(cur)
    conn.commit()

    queries = [
        (
            "1. Разделить кампании на три группы по сумме покупок (NTILE)",
            """WITH campaign_totals AS (
    SELECT campaign_id, SUM(purchase_amount) AS total_sales
    FROM marketing_data
    GROUP BY campaign_id
)
SELECT
    campaign_id,
    total_sales,
    NTILE(3) OVER (ORDER BY total_sales) AS sales_group
FROM campaign_totals
ORDER BY sales_group, total_sales;""",
        ),
        (
            "2. Последующая покупка внутри каждой рекламной кампании (LEAD)",
            """SELECT
    campaign_id,
    customer_id,
    purchase_amount,
    purchase_date,
    LEAD(purchase_amount) OVER (PARTITION BY campaign_id ORDER BY purchase_date) AS next_purchase_amount,
    LEAD(purchase_date) OVER (PARTITION BY campaign_id ORDER BY purchase_date) AS next_purchase_date
FROM marketing_data
ORDER BY campaign_id, purchase_date;""",
        ),
        (
            "3. Три первых клиента, привлечённых в рамках каждой кампании (LEAD)",
            """WITH ordered AS (
    SELECT
        campaign_id,
        customer_id,
        purchase_date,
        ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY purchase_date) AS rn,
        LEAD(customer_id, 1) OVER (PARTITION BY campaign_id ORDER BY purchase_date) AS second_customer_id,
        LEAD(customer_id, 2) OVER (PARTITION BY campaign_id ORDER BY purchase_date) AS third_customer_id
    FROM marketing_data
)
SELECT campaign_id, customer_id AS first_customer_id, second_customer_id, third_customer_id
FROM ordered
WHERE rn = 1
ORDER BY campaign_id;""",
        ),
        (
            "4. Первый клиент, привлечённый в рамках каждой кампании (FIRST_VALUE)",
            """SELECT DISTINCT
    campaign_id,
    FIRST_VALUE(customer_id) OVER (PARTITION BY campaign_id ORDER BY purchase_date) AS first_customer_id
FROM marketing_data
ORDER BY campaign_id;""",
        ),
        (
            "5. Первые клиенты, совершившие покупки в каждом канале (FIRST_VALUE)",
            """SELECT DISTINCT
    channel,
    FIRST_VALUE(customer_id) OVER (PARTITION BY channel ORDER BY purchase_date) AS first_customer_id
FROM marketing_data
ORDER BY channel;""",
        ),
        (
            "6. Последние клиенты, совершившие покупки в каждом канале (FIRST_VALUE с обратной сортировкой)",
            """SELECT DISTINCT
    channel,
    FIRST_VALUE(customer_id) OVER (PARTITION BY channel ORDER BY purchase_date DESC) AS last_customer_id
FROM marketing_data
ORDER BY channel;""",
        ),
        (
            "7. Два последних клиента, привлечённых в рамках каждой кампании (LAG)",
            """WITH ordered AS (
    SELECT
        campaign_id,
        customer_id,
        purchase_date,
        ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY purchase_date DESC) AS rn,
        LAG(customer_id, 1) OVER (PARTITION BY campaign_id ORDER BY purchase_date DESC) AS second_last_customer_id
    FROM marketing_data
)
SELECT campaign_id, customer_id AS last_customer_id, second_last_customer_id
FROM ordered
WHERE rn = 1
ORDER BY campaign_id;""",
        ),
        (
            "8. Последний клиент, привлечённый в рамках каждой кампании (FIRST_VALUE с обратной сортировкой)",
            """SELECT DISTINCT
    campaign_id,
    FIRST_VALUE(customer_id) OVER (PARTITION BY campaign_id ORDER BY purchase_date DESC) AS last_customer_id
FROM marketing_data
ORDER BY campaign_id;""",
        ),
        (
            "9. Последние клиенты, совершившие покупки в каждом регионе (FIRST_VALUE с обратной сортировкой)",
            """SELECT DISTINCT
    region,
    FIRST_VALUE(customer_id) OVER (PARTITION BY region ORDER BY purchase_date DESC) AS last_customer_id
FROM marketing_data
ORDER BY region;""",
        ),
        (
            "10. Пять первых покупок внутри каждой кампании и динамика",
            """WITH numbered AS (
    SELECT
        campaign_id,
        purchase_date,
        purchase_amount,
        ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY purchase_date) AS rn
    FROM marketing_data
)
SELECT
    campaign_id,
    MAX(CASE WHEN rn = 1 THEN purchase_amount END) AS purchase_1,
    MAX(CASE WHEN rn = 2 THEN purchase_amount END) AS purchase_2,
    MAX(CASE WHEN rn = 3 THEN purchase_amount END) AS purchase_3,
    MAX(CASE WHEN rn = 4 THEN purchase_amount END) AS purchase_4,
    MAX(CASE WHEN rn = 5 THEN purchase_amount END) AS purchase_5,
    ROUND(MAX(CASE WHEN rn = 1 THEN purchase_amount END) +
          COALESCE(MAX(CASE WHEN rn = 2 THEN purchase_amount END), 0) +
          COALESCE(MAX(CASE WHEN rn = 3 THEN purchase_amount END), 0) +
          COALESCE(MAX(CASE WHEN rn = 4 THEN purchase_amount END), 0) +
          COALESCE(MAX(CASE WHEN rn = 5 THEN purchase_amount END), 0), 2) AS sum_first_5
FROM numbered
WHERE rn <= 5
GROUP BY campaign_id
ORDER BY campaign_id;""",
        ),
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        prn(out, "ДОМАШНЕЕ ЗАДАНИЕ: ФУНКЦИИ РАНЖИРОВАНИЯ И СМЕЩЕНИЯ (ОКОННЫЕ ФУНКЦИИ)")
        prn(out, "NTILE, LEAD, LAG, FIRST_VALUE, LAST_VALUE. Данные: marketing_data.csv")
        prn(out, "")

        for i, (title, sql) in enumerate(queries, 1):
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
