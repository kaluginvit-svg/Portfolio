# -*- coding: utf-8 -*-
"""
Домашнее задание: функции для работы с датой и числами.
Данные: подкаталог «Файлы урока» — students.csv, results.csv, new_results.csv (для подсчёта бланков).
Результат — date_functions_homework_results.txt с полными SQL-запросами и выводом.
"""
import sqlite3
import csv
import os
import glob

DB_PATH = "date_functions_homework.db"
OUTPUT_PATH = "date_functions_homework_results.txt"


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
    pattern = os.path.join(base, "*", "students.csv")
    found = glob.glob(pattern)
    if not found:
        _prn(output, "Ошибка: не найден подкаталог с students.csv («Файлы урока»).")
        return
    data_dir = os.path.dirname(found[0])

    conn = sqlite3.connect(os.path.join(script_dir, DB_PATH))
    cur = conn.cursor()

    # Таблица students
    cur.execute("DROP TABLE IF EXISTS students")
    cur.execute("""
        CREATE TABLE students (
            student_id TEXT, full_name TEXT, birth_date TEXT, school_number INTEGER,
            average_grade REAL, city TEXT, district TEXT
        )
    """)
    with open(os.path.join(data_dir, "students.csv"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sn = row.get("school_number", "").strip()
            ag = row.get("average_grade", "").strip()
            cur.execute(
                "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?)",
                (row.get("student_id"), row.get("full_name"), row.get("birth_date"),
                 int(sn) if sn else None, float(ag) if ag else None, row.get("city"), row.get("district")),
            )

    # Таблица results (для подсчёта проверенных бланков по дате проверки)
    cur.execute("DROP TABLE IF EXISTS results")
    cur.execute("CREATE TABLE results (blanc_id TEXT, result INTEGER, check_date TEXT, inspector TEXT)")
    p = os.path.join(data_dir, "results.csv")
    if os.path.isfile(p):
        with open(p, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rv = row.get("result", "").strip()
                cur.execute("INSERT INTO results VALUES (?, ?, ?, ?)",
                    (row.get("blanc_id"), int(rv) if rv else None, row.get("check_date"), row.get("inspector")),
                )
    cur.execute("DROP TABLE IF EXISTS new_results")
    cur.execute("CREATE TABLE new_results (blanc_id TEXT, result INTEGER, check_date TEXT, inspector TEXT)")
    p2 = os.path.join(data_dir, "new_results.csv")
    if os.path.isfile(p2):
        with open(p2, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rv = row.get("result", "").strip()
                cur.execute("INSERT INTO new_results VALUES (?, ?, ?, ?)",
                    (row.get("blanc_id"), int(rv) if rv else None, row.get("check_date"), row.get("inspector")),
                )
    conn.commit()

    _prn(output, "ДОМАШНЕЕ ЗАДАНИЕ: ФУНКЦИИ ДЛЯ РАБОТЫ С ДАТОЙ И ЧИСЛАМИ")
    _prn(output, "Урок: преобразование дат, разница между датами, округление/усечение дат, подсчёт за период.")
    _prn(output, "Источник: «Файлы урока» — students.csv, results.csv, new_results.csv.")
    _prn(output, "")

    tasks = [
        (
            "1. Преобразовать строку «2024-06-11 10:00:00» в дату и время, вычесть 10 дней, отобразить результат",
            "Функция datetime(): первый аргумент — строка даты-времени, модификатор '-10 days' вычитает 10 дней.",
            """SELECT
  datetime('2024-06-11 10:00:00') AS исходная_дата_время,
  datetime('2024-06-11 10:00:00', '-10 days') AS минус_10_дней;""",
        ),
        (
            "2. Добавить к текущей дате и времени: 2 минуты, 2 часа, 2 дня, 2 месяца, 2 года",
            "Функция datetime('now', modifier): модификаторы '+2 minutes', '+2 hours', '+2 days', '+2 months', '+2 years'.",
            """SELECT
  datetime('now') AS текущая_дата_время,
  datetime('now', '+2 minutes') AS плюс_2_минуты,
  datetime('now', '+2 hours') AS плюс_2_часа,
  datetime('now', '+2 days') AS плюс_2_дня,
  datetime('now', '+2 months') AS плюс_2_месяца,
  datetime('now', '+2 years') AS плюс_2_года;""",
        ),
        (
            "3. Количество проверенных бланков в день / в месяц / в год",
            "Все проверки: results UNION ALL new_results. Группировка по date(check_date) — по дню; по strftime('%Y-%m', check_date) — по месяцу; по strftime('%Y', check_date) — по году. COUNT(*).",
            """-- По дням (пример: первые 15 записей)
SELECT date(check_date) AS день, COUNT(*) AS бланков_за_день
FROM (SELECT check_date FROM results UNION ALL SELECT check_date FROM new_results) t
WHERE check_date IS NOT NULL AND trim(check_date) != ''
GROUP BY date(check_date)
ORDER BY день
LIMIT 15;

-- По месяцам
SELECT strftime('%Y-%m', check_date) AS месяц, COUNT(*) AS бланков_за_месяц
FROM (SELECT check_date FROM results UNION ALL SELECT check_date FROM new_results) t
WHERE check_date IS NOT NULL AND trim(check_date) != ''
GROUP BY strftime('%Y-%m', check_date)
ORDER BY месяц;

-- По годам
SELECT strftime('%Y', check_date) AS год, COUNT(*) AS бланков_за_год
FROM (SELECT check_date FROM results UNION ALL SELECT check_date FROM new_results) t
WHERE check_date IS NOT NULL AND trim(check_date) != ''
GROUP BY strftime('%Y', check_date)
ORDER BY год;""",
        ),
        (
            "4. Извлечь из даты рождения школьников месяц и посчитать, сколько школьников родилось в данном месяце",
            "Функция strftime('%m', birth_date) извлекает номер месяца. GROUP BY месяц, COUNT(*).",
            """SELECT
  strftime('%m', birth_date) AS месяц_номер,
  COUNT(*) AS количество_школьников
FROM students
WHERE birth_date IS NOT NULL AND trim(birth_date) != ''
GROUP BY strftime('%m', birth_date)
ORDER BY месяц_номер;""",
        ),
        (
            "5. Усечь дату рождения студентов до начала года и вернуть имена вместе с усечённой датой",
            "Усечение до начала года: date(birth_date, 'start of year') в SQLite возвращает первый день года для данной даты.",
            """SELECT
  full_name AS имя,
  birth_date AS дата_рождения_исходная,
  date(birth_date, 'start of year') AS дата_усечённая_до_начала_года
FROM students
WHERE birth_date IS NOT NULL AND trim(birth_date) != ''
ORDER BY full_name
LIMIT 25;""",
        ),
        (
            "6. Вычислить возраст каждого студента на дату (текущая дата + 365 дней) и отобразить имя и возраст в будущем году",
            "Возраст в полных годах: (julianday('now', '+365 days') - julianday(birth_date)) / 365.25 с округлением вниз; либо разница лет через strftime.",
            """SELECT
  full_name AS имя,
  birth_date AS дата_рождения,
  CAST((julianday('now', '+365 days') - julianday(birth_date)) / 365.25 AS INTEGER) AS возраст_через_год
FROM students
WHERE birth_date IS NOT NULL AND trim(birth_date) != ''
ORDER BY full_name;""",
        ),
    ]

    # Задание 3 — три отдельных запроса (по дням с LIMIT, по месяцам, по годам)
    task3_queries = [
        ("3a. Проверенные бланки по дням (первые 15 строк)",
         """SELECT date(check_date) AS день, COUNT(*) AS бланков_за_день
FROM (SELECT check_date FROM results UNION ALL SELECT check_date FROM new_results) t
WHERE check_date IS NOT NULL AND trim(check_date) != ''
GROUP BY date(check_date)
ORDER BY день
LIMIT 15;"""),
        ("3b. Проверенные бланки по месяцам",
         """SELECT strftime('%Y-%m', check_date) AS месяц, COUNT(*) AS бланков_за_месяц
FROM (SELECT check_date FROM results UNION ALL SELECT check_date FROM new_results) t
WHERE check_date IS NOT NULL AND trim(check_date) != ''
GROUP BY strftime('%Y-%m', check_date)
ORDER BY месяц;"""),
        ("3c. Проверенные бланки по годам",
         """SELECT strftime('%Y', check_date) AS год, COUNT(*) AS бланков_за_год
FROM (SELECT check_date FROM results UNION ALL SELECT check_date FROM new_results) t
WHERE check_date IS NOT NULL AND trim(check_date) != ''
GROUP BY strftime('%Y', check_date)
ORDER BY год;"""),
    ]

    for title, comment, sql in tasks:
        if title.startswith("3."):
            _prn(output, "\n" + "=" * 60)
            _prn(output, title)
            _prn(output, "=" * 60)
            _prn(output, "Комментарий:", comment)
            _prn(output, "SQL (полный запрос):")
            _prn(output, sql.strip())
            _prn(output, "")
            for subtitle, subsql in task3_queries:
                _prn(output, "--- " + subtitle + " ---")
                cur.execute(subsql)
                _format_table(output, cur)
            continue
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
