# -*- coding: utf-8 -*-
"""
Домашнее задание: JOIN и UNION по таблицам «Пациенты», «Диагнозы», «Посещения».
Данные из подкаталога «Файлы ДЗ»: patients.csv, diagnoses.csv, visits.csv, visits2.csv.
Результаты с полным SQL и выводом — в visits_homework_results.txt.
"""
import sqlite3
import csv
import os
import glob

DB_PATH = "visits_homework.db"
OUTPUT_PATH = "visits_homework_results.txt"


def _prn(output, *a, **k):
    print(*a, **k, file=output)


def _format_table(output, cur):
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
    base = os.path.abspath(script_dir)

    # Поиск подкаталога «Файлы ДЗ» по наличию patients.csv
    pattern = os.path.join(base, "*", "patients.csv")
    found = glob.glob(pattern)
    if not found:
        _prn(output, "Ошибка: не найден подкаталог с patients.csv (ожидается «Файлы ДЗ»).")
        return
    data_dir = os.path.dirname(found[0])

    conn = sqlite3.connect(os.path.join(script_dir, DB_PATH))
    cur = conn.cursor()

    # Таблица «Пациенты»: patient_id, full_name, birth_date, city, district
    cur.execute("DROP TABLE IF EXISTS patients")
    cur.execute("""
        CREATE TABLE patients (
            patient_id TEXT,
            full_name TEXT,
            birth_date TEXT,
            city TEXT,
            district TEXT
        )
    """)
    with open(os.path.join(data_dir, "patients.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                "INSERT INTO patients VALUES (?, ?, ?, ?, ?)",
            (row.get("patient_id"), row.get("full_name"), row.get("birth_date"), row.get("city"), row.get("district")),
            )

    # Таблица «Диагнозы»: visit_id, diagnosis, treatment_plan, doctor_name
    cur.execute("DROP TABLE IF EXISTS diagnoses")
    cur.execute("""
        CREATE TABLE diagnoses (
            visit_id TEXT,
            diagnosis TEXT,
            treatment_plan TEXT,
            doctor_name TEXT
        )
    """)
    with open(os.path.join(data_dir, "diagnoses.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                "INSERT INTO diagnoses VALUES (?, ?, ?, ?)",
                (row.get("visit_id"), row.get("diagnosis"), row.get("treatment_plan"), row.get("doctor_name")),
            )

    # Таблица «Посещения» (visits.csv): patient_id, visit_id, visit_date, doctor_specialty
    cur.execute("DROP TABLE IF EXISTS visits")
    cur.execute("""
        CREATE TABLE visits (
            patient_id TEXT,
            visit_id TEXT,
            visit_date TEXT,
            doctor_specialty TEXT
        )
    """)
    path1 = os.path.join(data_dir, "visits.csv")
    if os.path.isfile(path1):
        with open(path1, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute(
                    "INSERT INTO visits VALUES (?, ?, ?, ?)",
                    (row.get("patient_id"), row.get("visit_id"), row.get("visit_date"), row.get("doctor_specialty")),
                )

    # Таблица «Посещения с дополнительными данными» (visits2.csv) — та же структура
    cur.execute("DROP TABLE IF EXISTS visits2")
    cur.execute("""
        CREATE TABLE visits2 (
            patient_id TEXT,
            visit_id TEXT,
            visit_date TEXT,
            doctor_specialty TEXT
        )
    """)
    path2 = os.path.join(data_dir, "visits2.csv")
    if os.path.isfile(path2):
        with open(path2, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute(
                    "INSERT INTO visits2 VALUES (?, ?, ?, ?)",
                    (row.get("patient_id"), row.get("visit_id"), row.get("visit_date"), row.get("doctor_specialty")),
                )

    conn.commit()

    # Заголовок отчёта
    _prn(output, "ДОМАШНЕЕ ЗАДАНИЕ: JOIN И UNION — ПАЦИЕНТЫ, ДИАГНОЗЫ, ПОСЕЩЕНИЯ")
    _prn(output, "Источник: подкаталог «Файлы ДЗ» — patients.csv, diagnoses.csv, visits.csv, visits2.csv.")
    _prn(output, "Таблицы: Пациенты (patient_id, full_name, birth_date, city, district);")
    _prn(output, "          Диагнозы (visit_id, diagnosis, treatment_plan, doctor_name);")
    _prn(output, "          Посещения visits и visits2 (patient_id, visit_id, visit_date, doctor_specialty).")
    _prn(output, "")

    tasks = [
        (
            "1. Все пациенты, которые посетили «Кардиолога», и их данные из таблицы «Пациенты»",
            "Объединяем все посещения (visits UNION ALL visits2), JOIN с patients по patient_id, фильтр doctor_specialty = 'Кардиолог', DISTINCT по пациенту.",
            """SELECT DISTINCT p.patient_id, p.full_name, p.birth_date, p.city, p.district
FROM patients p
INNER JOIN (
  SELECT patient_id, visit_id, visit_date, doctor_specialty FROM visits
  UNION ALL
  SELECT patient_id, visit_id, visit_date, doctor_specialty FROM visits2
) v ON p.patient_id = v.patient_id
WHERE v.doctor_specialty = 'Кардиолог'
ORDER BY p.patient_id""",
        ),
        (
            "2. Все визиты пациентов с диагнозом «ОРВИ»: информация о визитах и о пациентах",
            "JOIN диагнозов (diagnoses) с объединёнными посещениями (visits UNION ALL visits2) по visit_id и с пациентами (patients) по patient_id; фильтр diagnosis = 'ОРВИ'.",
            """SELECT v.visit_id, v.patient_id, v.visit_date, v.doctor_specialty,
       d.diagnosis, d.treatment_plan, d.doctor_name,
       p.full_name, p.birth_date, p.city, p.district
FROM diagnoses d
INNER JOIN (
  SELECT patient_id, visit_id, visit_date, doctor_specialty FROM visits
  UNION ALL
  SELECT patient_id, visit_id, visit_date, doctor_specialty FROM visits2
) v ON d.visit_id = v.visit_id
INNER JOIN patients p ON v.patient_id = p.patient_id
WHERE d.diagnosis = 'ОРВИ'
ORDER BY v.visit_date, v.visit_id""",
        ),
        (
            "3. Объединить все визиты",
            "Оператор UNION ALL: все строки из таблицы «Посещения» (visits) и таблицы «Посещения с дополнительными данными» (visits2) в одном результате.",
            """SELECT patient_id, visit_id, visit_date, doctor_specialty
FROM visits
UNION ALL
SELECT patient_id, visit_id, visit_date, doctor_specialty
FROM visits2
ORDER BY visit_date, visit_id""",
        ),
    ]

    for title, comment, sql in tasks:
        _prn(output, "\n" + "=" * 60)
        _prn(output, title)
        _prn(output, "=" * 60)
        _prn(output, "Комментарий:", comment)
        _prn(output, "SQL (полная команда):")
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
