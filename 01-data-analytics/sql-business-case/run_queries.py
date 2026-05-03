# -*- coding: utf-8 -*-
"""
Скрипт загружает CSV в SQLite и выполняет все SQL-запросы,
сохраняя полный вывод каждого запроса в отдельный .txt файл.
"""
import sqlite3
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_DIR = os.path.join(BASE_DIR, "sql")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DB_PATH = os.path.join(BASE_DIR, "pharma.db")

def load_csv_to_sqlite(conn):
    """Загрузка customers.csv и pharma_orders.csv в SQLite."""
    cursor = conn.cursor()
    
    # Таблица клиентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER,
            date_of_birth TEXT,
            first_name TEXT,
            last_name TEXT,
            second_name TEXT,
            gender TEXT
        )
    """)
    conn.commit()
    
    with open(os.path.join(BASE_DIR, "customers.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cursor.executemany(
            "INSERT INTO customers VALUES (:customer_id, :date_of_birth, :first_name, :last_name, :second_name, :gender)",
            [row for row in reader]
        )
    
    # Таблица заказов (в CSV колонка drug, не drug_name)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pharma_orders (
            pharmacy_name TEXT,
            order_id INTEGER,
            drug TEXT,
            price INTEGER,
            count INTEGER,
            city TEXT,
            report_date TEXT,
            customer_id INTEGER
        )
    """)
    conn.commit()
    
    with open(os.path.join(BASE_DIR, "pharma_orders.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cursor.executemany(
            """INSERT INTO pharma_orders VALUES (
                :pharmacy_name, :order_id, :drug, :price, :count, :city, :report_date, :customer_id
            )""",
            [row for row in reader]
        )
    
    conn.commit()
    print("Данные загружены в SQLite.")

def _format_table(col_names, rows, sep="  "):
    """Форматирует заголовок и строки в таблицу с выравниванием колонок (числа по правому краю)."""
    def cell_str(x):
        return "" if x is None else str(x)

    header = list(col_names)
    data = [[cell_str(v) for v in row] for row in rows]
    ncols = len(header)

    # Ширина каждой колонки
    widths = []
    for j in range(ncols):
        col_widths = [len(header[j])] + [len(data[i][j]) for i in range(len(data))]
        widths.append(max(col_widths))

    def looks_numeric(cells):
        if not cells:
            return False
        for s in cells:
            s = s.strip()
            if not s:
                continue
            try:
                float(s.replace(" ", "").replace(",", "."))
            except ValueError:
                return False
        return True

    # Числовая колонка: все значения в данных — числа (заголовок не учитываем)
    is_numeric = [looks_numeric([data[i][j] for i in range(len(data))]) for j in range(ncols)]

    def pad(s, j):
        w = widths[j]
        return s.rjust(w) if is_numeric[j] else s.ljust(w)

    result = []
    result.append(sep.join(pad(header[j], j) for j in range(ncols)))
    result.append("-" * (sum(widths) + (ncols - 1) * len(sep)))
    for i in range(len(data)):
        result.append(sep.join(pad(data[i][j], j) for j in range(ncols)))
    return "\n".join(result)

def run_query_and_save(conn, sql_path, result_path):
    """Выполняет SQL из файла и сохраняет текст запроса + все строки результата в .txt."""
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_full = f.read()
    # Убрать только комментарии для выполнения (оставить один блок запроса)
    lines = sql_full.split("\n")
    query_lines = []
    for line in lines:
        s = line.strip()
        if s.startswith("--") or not s:
            continue
        query_lines.append(line)
    query = "\n".join(query_lines)
    
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    col_names = [d[0] for d in cursor.description]
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as out:
        out.write("=== Текст запроса ===\n\n")
        out.write(sql_full.strip())
        out.write("\n\n=== Результат ===\n\n")
        out.write(_format_table(col_names, rows))
        out.write(f"\n\nВсего строк: {len(rows)}\n")
    
    print(f"  {os.path.basename(result_path)}: {len(rows)} строк")
    return len(rows)

def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    load_csv_to_sqlite(conn)
    
    queries = [
        ("01_top3_pharmacies.sql", "01_top3_pharmacies.txt"),
        ("02_top3_drugs.sql", "02_top3_drugs.txt"),
        ("03_pharmacies_over_18m.sql", "03_pharmacies_over_18m.txt"),
        ("04_cumulative_sales_by_pharmacy.sql", "04_cumulative_sales_by_pharmacy.txt"),
        ("05_customers_per_pharmacy.sql", "05_customers_per_pharmacy.txt"),
        ("06_best_customers.sql", "06_best_customers.txt"),
        ("07_cumulative_sum_by_customer.sql", "07_cumulative_sum_by_customer.txt"),
        ("08_top_customers_gorzdrav_zdravcity.sql", "08_top_customers_gorzdrav_zdravcity.txt"),
    ]
    
    print("Выполнение запросов и сохранение результатов:")
    for sql_name, txt_name in queries:
        run_query_and_save(
            conn,
            os.path.join(SQL_DIR, sql_name),
            os.path.join(RESULTS_DIR, txt_name),
        )
    
    conn.close()
    print("Готово. Результаты в папке results/")

if __name__ == "__main__":
    main()
