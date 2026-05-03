# -*- coding: utf-8 -*-
"""
Домашнее задание: переписать запросы с подзапросов на временные таблицы (CREATE TEMP TABLE).
Те же 7 заданий, данные из подкаталога «Файлы урока».
Итог — один .txt с полными SQL-командами и результатами.
"""
import sqlite3
import csv
import os
import glob

DB_PATH = "subqueries_homework.db"
OUTPUT_PATH = "temp_tables_homework_results.txt"


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


def _run_statements(cur, statements):
    """Выполняет список SQL-операторов по порядку. Результат последнего SELECT доступен в cur."""
    for sql in statements:
        cur.execute(sql)


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

    # Загрузка данных (как в run_subqueries_homework.py)
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

    cur.execute("DROP TABLE IF EXISTS exams")
    cur.execute("""
        CREATE TABLE exams (
            student_id TEXT, blanc_id TEXT, subject TEXT, exam_date TEXT, duration REAL
        )
    """)
    with open(os.path.join(data_dir, "exams.csv"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = row.get("duration", "").strip()
            cur.execute(
                "INSERT INTO exams VALUES (?, ?, ?, ?, ?)",
                (row.get("student_id"), row.get("blanc_id"), row.get("subject"), row.get("exam_date"), float(d) if d else None),
            )

    cur.execute("DROP TABLE IF EXISTS results")
    cur.execute("CREATE TABLE results (blanc_id TEXT, result INTEGER, check_date TEXT, inspector TEXT)")
    with open(os.path.join(data_dir, "results.csv"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rv = row.get("result", "").strip()
            cur.execute("INSERT INTO results VALUES (?, ?, ?, ?)",
                (row.get("blanc_id"), int(rv) if rv else None, row.get("check_date"), row.get("inspector")),
            )

    cur.execute("DROP TABLE IF EXISTS new_results")
    cur.execute("CREATE TABLE new_results (blanc_id TEXT, result INTEGER, check_date TEXT, inspector TEXT)")
    with open(os.path.join(data_dir, "new_results.csv"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rv = row.get("result", "").strip()
            cur.execute("INSERT INTO new_results VALUES (?, ?, ?, ?)",
                (row.get("blanc_id"), int(rv) if rv else None, row.get("check_date"), row.get("inspector")),
            )
    conn.commit()

    _prn(output, "ДОМАШНЕЕ ЗАДАНИЕ: ВРЕМЕННЫЕ ТАБЛИЦЫ (ВМЕСТО ПОДЗАПРОСОВ)")
    _prn(output, "Переписано с предыдущего урока: те же 7 заданий, реализация через CREATE TEMP TABLE.")
    _prn(output, "Источник: подкаталог «Файлы урока» — students.csv, exams.csv, results.csv, new_results.csv.")
    _prn(output, "")

    # Задание 1: имена студентов, сдававших английский
    task1_sql = """-- Временная таблица: студенты, сдававшие английский
CREATE TEMP TABLE IF NOT EXISTS tmp_english_students AS
SELECT DISTINCT student_id FROM exams WHERE subject = 'Английский';

SELECT s.full_name
FROM students s
INNER JOIN tmp_english_students t ON s.student_id = t.student_id
ORDER BY s.full_name;"""

    # Задание 2: школы, где средний балл ниже среднего по всем школам
    task2_sql = """-- Временная таблица: средний балл по всем
CREATE TEMP TABLE IF NOT EXISTS tmp_overall_avg AS
SELECT AVG(average_grade) AS overall_avg FROM students;

-- Временная таблица: средний по каждой школе
CREATE TEMP TABLE IF NOT EXISTS tmp_school_avg AS
SELECT school_number, ROUND(AVG(average_grade), 2) AS avg_grade
FROM students WHERE school_number IS NOT NULL GROUP BY school_number;

SELECT t.school_number AS school, t.avg_grade
FROM tmp_school_avg t, tmp_overall_avg o
WHERE t.avg_grade < o.overall_avg
ORDER BY t.avg_grade;"""

    # Задание 3: самый «злой» проверяющий
    task3_sql = """-- Все результаты (results + new_results)
CREATE TEMP TABLE IF NOT EXISTS tmp_all_results AS
SELECT result, inspector FROM results
UNION ALL SELECT result, inspector FROM new_results;

-- Средний балл по каждому инспектору
CREATE TEMP TABLE IF NOT EXISTS tmp_inspector_avg AS
SELECT inspector, AVG(result) AS avg_result FROM tmp_all_results GROUP BY inspector;

-- Минимальный средний балл
CREATE TEMP TABLE IF NOT EXISTS tmp_min_avg AS
SELECT MIN(avg_result) AS m FROM tmp_inspector_avg;

SELECT i.inspector, ROUND(i.avg_result, 2) AS avg_result
FROM tmp_inspector_avg i, tmp_min_avg m
WHERE i.avg_result = m.m;"""

    # Задание 4: результаты ниже среднего по всем бланкам
    task4_sql = """-- Все бланки с результатами
CREATE TEMP TABLE IF NOT EXISTS tmp_all_blancs AS
SELECT blanc_id, result, check_date, inspector FROM results
UNION ALL SELECT blanc_id, result, check_date, inspector FROM new_results;

-- Средний балл по всем бланкам
CREATE TEMP TABLE IF NOT EXISTS tmp_avg_result AS
SELECT AVG(result) AS avg_r FROM tmp_all_blancs;

SELECT b.blanc_id, b.result, b.check_date, b.inspector
FROM tmp_all_blancs b, tmp_avg_result a
WHERE b.result < a.avg_r
ORDER BY b.result;"""

    # Задание 5: студенты с баллом выше среднего по городу
    task5_sql = """-- Средний балл по каждому городу
CREATE TEMP TABLE IF NOT EXISTS tmp_city_avg AS
SELECT city, AVG(average_grade) AS city_avg FROM students GROUP BY city;

SELECT s.full_name, s.school_number AS school, s.city, ROUND(s.average_grade, 2) AS average_grade
FROM students s
INNER JOIN tmp_city_avg c ON s.city = c.city
WHERE s.average_grade > c.city_avg
ORDER BY s.average_grade DESC, s.full_name;"""

    # Задание 6: предметы с средним результатом выше общего
    task6_sql = """-- Все результаты по бланкам (для соединения с exams)
CREATE TEMP TABLE IF NOT EXISTS tmp_blanc_results AS
SELECT blanc_id, result FROM results
UNION ALL SELECT blanc_id, result FROM new_results;

-- Средний результат по каждому предмету
CREATE TEMP TABLE IF NOT EXISTS tmp_subject_avg AS
SELECT e.subject, AVG(r.result) AS avg_result
FROM exams e INNER JOIN tmp_blanc_results r ON e.blanc_id = r.blanc_id
GROUP BY e.subject;

-- Общий средний результат по всем предметам
CREATE TEMP TABLE IF NOT EXISTS tmp_overall_result AS
SELECT AVG(result) AS overall FROM tmp_blanc_results;

SELECT s.subject, ROUND(s.avg_result, 2) AS avg_result
FROM tmp_subject_avg s, tmp_overall_result o
WHERE s.avg_result > o.overall
ORDER BY s.avg_result DESC;"""

    # Задание 7: студенты, сдавшие экзамен по каждому предмету в период 2024-06-01..2024-06-15
    task7_sql = """-- Общее количество предметов
CREATE TEMP TABLE IF NOT EXISTS tmp_total_subjects AS
SELECT COUNT(DISTINCT subject) AS cnt FROM exams;

-- По каждому студенту: сколько разных предметов сдано в периоде
CREATE TEMP TABLE IF NOT EXISTS tmp_student_in_period AS
SELECT student_id, COUNT(DISTINCT subject) AS cnt
FROM exams
WHERE date(exam_date) >= '2024-06-01' AND date(exam_date) <= '2024-06-15'
GROUP BY student_id;

SELECT s.full_name
FROM students s
INNER JOIN tmp_student_in_period t ON s.student_id = t.student_id
CROSS JOIN tmp_total_subjects tot
WHERE t.cnt = tot.cnt
ORDER BY s.full_name;"""

    tasks = [
        ("1. Имена студентов, сдававших экзамены по английскому языку",
         "Временная таблица tmp_english_students — student_id по предмету «Английский»; JOIN с students.",
         task1_sql,
         ["CREATE TEMP TABLE IF NOT EXISTS tmp_english_students AS SELECT DISTINCT student_id FROM exams WHERE subject = 'Английский'",
          "SELECT s.full_name FROM students s INNER JOIN tmp_english_students t ON s.student_id = t.student_id ORDER BY s.full_name"],
         ["tmp_english_students"]),
        ("2. Школы, в которых средний балл учеников ниже среднего по всем школам",
         "Временные таблицы: tmp_overall_avg (общий средний), tmp_school_avg (средний по школе); выборка по условию.",
         task2_sql,
         ["CREATE TEMP TABLE IF NOT EXISTS tmp_overall_avg AS SELECT AVG(average_grade) AS overall_avg FROM students",
          "CREATE TEMP TABLE IF NOT EXISTS tmp_school_avg AS SELECT school_number, ROUND(AVG(average_grade), 2) AS avg_grade FROM students WHERE school_number IS NOT NULL GROUP BY school_number",
          "SELECT t.school_number AS school, t.avg_grade FROM tmp_school_avg t, tmp_overall_avg o WHERE t.avg_grade < o.overall_avg ORDER BY t.avg_grade"],
         ["tmp_overall_avg", "tmp_school_avg"]),
        ("3. Самый «злой» проверяющий (инспектор с минимальным средним баллом)",
         "Временные таблицы: tmp_all_results (все проверки), tmp_inspector_avg (средний по инспектору), tmp_min_avg (минимум).",
         task3_sql,
         ["CREATE TEMP TABLE IF NOT EXISTS tmp_all_results AS SELECT result, inspector FROM results UNION ALL SELECT result, inspector FROM new_results",
          "CREATE TEMP TABLE IF NOT EXISTS tmp_inspector_avg AS SELECT inspector, AVG(result) AS avg_result FROM tmp_all_results GROUP BY inspector",
          "CREATE TEMP TABLE IF NOT EXISTS tmp_min_avg AS SELECT MIN(avg_result) AS m FROM tmp_inspector_avg",
          "SELECT i.inspector, ROUND(i.avg_result, 2) AS avg_result FROM tmp_inspector_avg i, tmp_min_avg m WHERE i.avg_result = m.m"],
         ["tmp_all_results", "tmp_inspector_avg", "tmp_min_avg"]),
        ("4. Результаты ниже среднего балла по всем бланкам",
         "Временные таблицы: tmp_all_blancs (все бланки), tmp_avg_result (средний); фильтр result < avg_r.",
         task4_sql,
         ["CREATE TEMP TABLE IF NOT EXISTS tmp_all_blancs AS SELECT blanc_id, result, check_date, inspector FROM results UNION ALL SELECT blanc_id, result, check_date, inspector FROM new_results",
          "CREATE TEMP TABLE IF NOT EXISTS tmp_avg_result AS SELECT AVG(result) AS avg_r FROM tmp_all_blancs",
          "SELECT b.blanc_id, b.result, b.check_date, b.inspector FROM tmp_all_blancs b, tmp_avg_result a WHERE b.result < a.avg_r ORDER BY b.result"],
         ["tmp_all_blancs", "tmp_avg_result"]),
        ("5. Студенты с средним баллом выше среднего по городу. ФИО, школа, город, средний балл",
         "Временная таблица tmp_city_avg — средний балл по городу; JOIN с students и условие average_grade > city_avg.",
         task5_sql,
         ["CREATE TEMP TABLE IF NOT EXISTS tmp_city_avg AS SELECT city, AVG(average_grade) AS city_avg FROM students GROUP BY city",
          "SELECT s.full_name, s.school_number AS school, s.city, ROUND(s.average_grade, 2) AS average_grade FROM students s INNER JOIN tmp_city_avg c ON s.city = c.city WHERE s.average_grade > c.city_avg ORDER BY s.average_grade DESC, s.full_name"],
         ["tmp_city_avg"]),
        ("6. Предметы, по которым средний результат выше общего среднего по всем предметам",
         "Временные таблицы: tmp_blanc_results, tmp_subject_avg (средний по предмету), tmp_overall_result (общий средний).",
         task6_sql,
         ["CREATE TEMP TABLE IF NOT EXISTS tmp_blanc_results AS SELECT blanc_id, result FROM results UNION ALL SELECT blanc_id, result FROM new_results",
          "CREATE TEMP TABLE IF NOT EXISTS tmp_subject_avg AS SELECT e.subject, AVG(r.result) AS avg_result FROM exams e INNER JOIN tmp_blanc_results r ON e.blanc_id = r.blanc_id GROUP BY e.subject",
          "CREATE TEMP TABLE IF NOT EXISTS tmp_overall_result AS SELECT AVG(result) AS overall FROM tmp_blanc_results",
          "SELECT s.subject, ROUND(s.avg_result, 2) AS avg_result FROM tmp_subject_avg s, tmp_overall_result o WHERE s.avg_result > o.overall ORDER BY s.avg_result DESC"],
         ["tmp_blanc_results", "tmp_subject_avg", "tmp_overall_result"]),
        ("7. Студенты, сдавшие экзамены по каждому предмету в период ('2024-06-01', '2024-06-15'). Вывести ФИО",
         "Временные таблицы: tmp_total_subjects (число предметов), tmp_student_in_period (по студенту — число предметов в периоде); CROSS JOIN и условие равенства.",
         task7_sql,
         ["CREATE TEMP TABLE IF NOT EXISTS tmp_total_subjects AS SELECT COUNT(DISTINCT subject) AS cnt FROM exams",
          "CREATE TEMP TABLE IF NOT EXISTS tmp_student_in_period AS SELECT student_id, COUNT(DISTINCT subject) AS cnt FROM exams WHERE date(exam_date) >= '2024-06-01' AND date(exam_date) <= '2024-06-15' GROUP BY student_id",
          "SELECT s.full_name FROM students s INNER JOIN tmp_student_in_period t ON s.student_id = t.student_id CROSS JOIN tmp_total_subjects tot WHERE t.cnt = tot.cnt ORDER BY s.full_name"],
         ["tmp_total_subjects", "tmp_student_in_period"]),
    ]

    for title, comment, full_sql, statements, drop_tables in tasks:
        _prn(output, "\n" + "=" * 60)
        _prn(output, title)
        _prn(output, "=" * 60)
        _prn(output, "Комментарий:", comment)
        _prn(output, "SQL (полная команда с временными таблицами):")
        _prn(output, full_sql.strip())
        _prn(output, "")
        for st in statements:
            cur.execute(st)
        _format_table(output, cur)
        for t in drop_tables:
            cur.execute("DROP TABLE IF EXISTS " + t)

    conn.close()
    _prn(output, "\nГотово.")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__)) or "."
    out_path = os.path.join(script_dir, OUTPUT_PATH)
    with open(out_path, "w", encoding="utf-8") as f:
        main(f)
    print("Результаты сохранены в", out_path)
