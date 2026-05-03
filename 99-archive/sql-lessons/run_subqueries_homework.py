# -*- coding: utf-8 -*-
"""
Домашнее задание: «Подзапросы к базам данных».
Данные из подкаталога «Файлы урока»: students.csv, exams.csv, results.csv, new_results.csv.
Итог — один .txt с полными SQL-запросами и результатами.
"""
import sqlite3
import csv
import os
import glob

DB_PATH = "subqueries_homework.db"
OUTPUT_PATH = "subqueries_homework_results.txt"


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
        _prn(output, "Ошибка: не найден подкаталог с students.csv (ожидается «Файлы урока»).")
        return
    data_dir = os.path.dirname(found[0])

    conn = sqlite3.connect(os.path.join(script_dir, DB_PATH))
    cur = conn.cursor()

    # students: student_id, full_name, birth_date, school_number, average_grade, city, district
    cur.execute("DROP TABLE IF EXISTS students")
    cur.execute("""
        CREATE TABLE students (
            student_id TEXT,
            full_name TEXT,
            birth_date TEXT,
            school_number INTEGER,
            average_grade REAL,
            city TEXT,
            district TEXT
        )
    """)
    with open(os.path.join(data_dir, "students.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sn = row.get("school_number", "").strip()
            sn = int(sn) if sn else None
            ag = row.get("average_grade", "").strip()
            ag = float(ag) if ag else None
            cur.execute(
                "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?)",
                (row.get("student_id"), row.get("full_name"), row.get("birth_date"), sn, ag, row.get("city"), row.get("district")),
            )

    # exams: student_id, blanc_id, subject, exam_date, duration
    cur.execute("DROP TABLE IF EXISTS exams")
    cur.execute("""
        CREATE TABLE exams (
            student_id TEXT,
            blanc_id TEXT,
            subject TEXT,
            exam_date TEXT,
            duration REAL
        )
    """)
    with open(os.path.join(data_dir, "exams.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = row.get("duration", "").strip()
            d = float(d) if d else None
            cur.execute(
                "INSERT INTO exams VALUES (?, ?, ?, ?, ?)",
                (row.get("student_id"), row.get("blanc_id"), row.get("subject"), row.get("exam_date"), d),
            )

    # results: blanc_id, result, check_date, inspector
    cur.execute("DROP TABLE IF EXISTS results")
    cur.execute("""
        CREATE TABLE results (
            blanc_id TEXT,
            result INTEGER,
            check_date TEXT,
            inspector TEXT
        )
    """)
    with open(os.path.join(data_dir, "results.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rv = row.get("result", "").strip()
            rv = int(rv) if rv else None
            cur.execute(
                "INSERT INTO results VALUES (?, ?, ?, ?)",
                (row.get("blanc_id"), rv, row.get("check_date"), row.get("inspector")),
            )

    cur.execute("DROP TABLE IF EXISTS new_results")
    cur.execute("""
        CREATE TABLE new_results (
            blanc_id TEXT,
            result INTEGER,
            check_date TEXT,
            inspector TEXT
        )
    """)
    with open(os.path.join(data_dir, "new_results.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rv = row.get("result", "").strip()
            rv = int(rv) if rv else None
            cur.execute(
                "INSERT INTO new_results VALUES (?, ?, ?, ?)",
                (row.get("blanc_id"), rv, row.get("check_date"), row.get("inspector")),
            )

    conn.commit()

    _prn(output, "ДОМАШНЕЕ ЗАДАНИЕ: ПОДЗАПРОСЫ К БАЗАМ ДАННЫХ")
    _prn(output, "Источник: подкаталог «Файлы урока» — students.csv, exams.csv, results.csv, new_results.csv.")
    _prn(output, "Таблицы: students (student_id, full_name, school_number, average_grade, city, ...);")
    _prn(output, "          exams (student_id, blanc_id, subject, exam_date, duration);")
    _prn(output, "          results, new_results (blanc_id, result, check_date, inspector).")
    _prn(output, "")

    tasks = [
        (
            "1. Имена студентов, сдававших экзамены по английскому языку",
            "Подзапрос / JOIN: выбираем студентов из exams с subject = 'Английский', выводим full_name из students.",
            """SELECT DISTINCT s.full_name
FROM students s
INNER JOIN exams e ON s.student_id = e.student_id
WHERE e.subject = 'Английский'
ORDER BY s.full_name""",
        ),
        (
            "2. Школы, в которых средний балл учеников ниже среднего по всем школам",
            "Подзапрос в HAVING: средний по всем — (SELECT AVG(average_grade) FROM students); по школе — GROUP BY school_number, HAVING AVG(average_grade) < подзапрос.",
            """SELECT school_number AS school, ROUND(AVG(average_grade), 2) AS avg_grade
FROM students
WHERE school_number IS NOT NULL
GROUP BY school_number
HAVING AVG(average_grade) < (SELECT AVG(average_grade) FROM students)
ORDER BY avg_grade""",
        ),
        (
            "3. Самый «злой» проверяющий (инспектор с минимальным средним баллом)",
            "Подзапрос в FROM: по каждому инспектору AVG(result) из results и new_results (UNION ALL), затем выбор с минимальным средним.",
            """SELECT inspector, ROUND(avg_result, 2) AS avg_result
FROM (
  SELECT inspector, AVG(result) AS avg_result
  FROM (
    SELECT blanc_id, result, inspector FROM results
    UNION ALL
    SELECT blanc_id, result, inspector FROM new_results
  ) all_res
  GROUP BY inspector
) t
WHERE avg_result = (SELECT MIN(avg_result) FROM (
  SELECT AVG(result) AS avg_result
  FROM (SELECT result, inspector FROM results UNION ALL SELECT result, inspector FROM new_results)
  GROUP BY inspector
))""",
        ),
        (
            "4. Результаты ниже среднего балла по всем бланкам (фильтрация)",
            "Подзапрос в WHERE: все бланки — results UNION ALL new_results; фильтр result < (SELECT AVG(result) FROM ...).",
            """SELECT blanc_id, result, check_date, inspector
FROM (
  SELECT blanc_id, result, check_date, inspector FROM results
  UNION ALL
  SELECT blanc_id, result, check_date, inspector FROM new_results
) all_res
WHERE result < (SELECT AVG(result) FROM (
  SELECT result FROM results UNION ALL SELECT result FROM new_results
))
ORDER BY result""",
        ),
        (
            "5. Студенты, у которых средний балл выше среднего по городу. ФИО, школа, город, средний балл",
            "Подзапросы: средний по студенту (из результатов экзаменов или average_grade); средний по городу; сравнение. Используем average_grade из students и подзапрос по городу.",
            """SELECT s.full_name, s.school_number AS school, s.city, ROUND(s.average_grade, 2) AS average_grade
FROM students s
WHERE s.average_grade > (
  SELECT AVG(average_grade) FROM students WHERE city = s.city
)
ORDER BY s.average_grade DESC, s.full_name""",
        ),
        (
            "6. Предметы, по которым средний результат выше общего среднего по всем предметам",
            "Подзапрос в HAVING: средний по предмету (exams JOIN все results) — GROUP BY subject; общий средний — (SELECT AVG(result) FROM ...); HAVING AVG(result) > общий.",
            """SELECT e.subject, ROUND(AVG(r.result), 2) AS avg_result
FROM exams e
INNER JOIN (
  SELECT blanc_id, result FROM results
  UNION ALL
  SELECT blanc_id, result FROM new_results
) r ON e.blanc_id = r.blanc_id
GROUP BY e.subject
HAVING AVG(r.result) > (SELECT AVG(result) FROM (SELECT result FROM results UNION ALL SELECT result FROM new_results))
ORDER BY avg_result DESC""",
        ),
        (
            "7. Студенты, сдавшие экзамены по каждому предмету в период ('2024-06-01', '2024-06-15'). Вывести ФИО",
            "Подзапрос: количество уникальных предметов в периоде по студенту должно равняться общему количеству предметов. Период — по дате (date(exam_date)) включительно.",
            """SELECT s.full_name
FROM students s
INNER JOIN exams e ON s.student_id = e.student_id
WHERE date(e.exam_date) >= '2024-06-01' AND date(e.exam_date) <= '2024-06-15'
GROUP BY s.student_id, s.full_name
HAVING COUNT(DISTINCT e.subject) = (SELECT COUNT(DISTINCT subject) FROM exams)
ORDER BY s.full_name""",
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
