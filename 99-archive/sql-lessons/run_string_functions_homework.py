# -*- coding: utf-8 -*-
"""
Домашнее задание: функции для работы со строками.
Данные: flights.csv (рейсы — airline, status, pilot_name, arrival_city, даты и т.д.).
Результат — string_functions_homework_results.txt с полным SQL и выводом по каждому заданию.
"""
import sqlite3
import csv
import os

DB_PATH = "string_functions_homework.db"
CSV_PATH = "flights.csv"
OUTPUT_PATH = "string_functions_homework_results.txt"


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
    csv_path = os.path.join(script_dir, CSV_PATH)
    if not os.path.isfile(csv_path):
        _prn(output, "Ошибка: файл flights.csv не найден.")
        return

    conn = sqlite3.connect(os.path.join(script_dir, DB_PATH))
    # Функция переворота строки (для задания 10)
    conn.create_function("reverse_str", 1, lambda s: (s[::-1] if s else None))
    # Функция «первые буквы заглавные» (для задания 9)
    conn.create_function("capitalize_words", 1, lambda s: (s.title() if s else None))
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS flights")
    cur.execute("""
        CREATE TABLE flights (
            flight_number TEXT,
            airline TEXT,
            departure_city TEXT,
            arrival_city TEXT,
            departure_time TEXT,
            arrival_time TEXT,
            status TEXT,
            aircraft_type TEXT,
            pilot_name TEXT
        )
    """)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                "INSERT INTO flights VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row.get("flight_number"),
                    row.get("airline"),
                    row.get("departure_city"),
                    row.get("arrival_city"),
                    row.get("departure_time"),
                    row.get("arrival_time"),
                    row.get("status"),
                    row.get("aircraft_type"),
                    row.get("pilot_name"),
                ),
            )
    conn.commit()

    _prn(output, "ДОМАШНЕЕ ЗАДАНИЕ: ФУНКЦИИ ДЛЯ РАБОТЫ СО СТРОКАМИ")
    _prn(output, "Урок: извлечение, изменение и объединение строк; применение в анализе данных.")
    _prn(output, "Источник: flights.csv (рейсы: airline, status, pilot_name, arrival_city, даты и др.).")
    _prn(output, "")

    tasks = [
        (
            "1. Длина названия авиакомпании (airline)",
            "Функция LENGTH(airline) возвращает число символов в строке.",
            "SELECT airline, LENGTH(airline) AS длина_названия FROM flights ORDER BY flight_number LIMIT 20;",
        ),
        (
            "2. Статус рейса (status) в верхнем регистре",
            "Функция UPPER(status) преобразует строку в верхний регистр.",
            "SELECT flight_number, status, UPPER(status) AS status_upper FROM flights ORDER BY flight_number LIMIT 20;",
        ),
        (
            "3. Имя пилота (pilot_name) в нижнем регистре",
            "Функция LOWER(pilot_name) преобразует строку в нижний регистр.",
            "SELECT flight_number, pilot_name, LOWER(pilot_name) AS pilot_name_lower FROM flights ORDER BY flight_number LIMIT 20;",
        ),
        (
            "4. Извлечь день и месяц из даты прилёта (arrival_time)",
            "Функция strftime('%d', ...) — день, strftime('%m', ...) — месяц (в SQLite дата в тексте обрабатывается через strftime).",
            """SELECT arrival_time,
  strftime('%d', arrival_time) AS день_прилёта,
  strftime('%m', arrival_time) AS месяц_прилёта
FROM flights
ORDER BY flight_number
LIMIT 20;""",
        ),
        (
            "5. Удалить пробелы с начала и конца названия города прибытия (arrival_city)",
            "Функция TRIM(arrival_city) удаляет пробелы с обоих концов строки.",
            "SELECT arrival_city, TRIM(arrival_city) AS arrival_city_trim FROM flights ORDER BY flight_number LIMIT 20;",
        ),
        (
            "6. Заменить все '-' на '.' в датах прилёта и вылета",
            "Функция REPLACE(строка, '-', '.') заменяет все вхождения дефиса на точку.",
            """SELECT
  departure_time AS вылет_исходная,
  REPLACE(departure_time, '-', '.') AS вылет_замена,
  arrival_time AS прилёт_исходная,
  REPLACE(arrival_time, '-', '.') AS прилёт_замена
FROM flights
ORDER BY flight_number
LIMIT 15;""",
        ),
        (
            "7. Объединить номер рейса и название самолёта в одну строку",
            "Оператор || объединяет строки. Конкатенация: flight_number || ' ' || aircraft_type.",
            """SELECT flight_number, aircraft_type,
  flight_number || ' ' || aircraft_type AS номер_и_самолёт
FROM flights
ORDER BY flight_number
LIMIT 20;""",
        ),
        (
            "8. Информационная строка «Рейс (номер) авиакомпании (авиакомпания), в статусе (status)»",
            "Конкатенация с литералами: 'Рейс ' || flight_number || ' авиакомпании ' || airline || ', в статусе ' || status.",
            """SELECT
  'Рейс ' || flight_number || ' авиакомпании ' || airline || ', в статусе ' || status AS информационная_строка
FROM flights
ORDER BY flight_number
LIMIT 15;""",
        ),
        (
            "9. Преобразовать название города прибытия в заглавные первые буквы (каждое слово)",
            "Пользовательская функция capitalize_words(s) — первые буквы слов заглавные (аналог INITCAP).",
            "SELECT arrival_city, capitalize_words(arrival_city) AS arrival_city_capitalized FROM flights ORDER BY flight_number LIMIT 20;",
        ),
        (
            "10. Перевернуть строку с датой отправления",
            "Пользовательская функция reverse_str(departure_time) возвращает строку в обратном порядке.",
            "SELECT departure_time, reverse_str(departure_time) AS departure_time_reversed FROM flights ORDER BY flight_number LIMIT 15;",
        ),
        (
            "11. Выделить имя, фамилию и отчество в отдельные поля по позициям пробелов",
            "INSTR(pilot_name, ' ') — позиция первого пробела; SUBSTR — подстроки до первого пробела, между пробелами, после второго.",
            """SELECT pilot_name,
  SUBSTR(pilot_name, 1, INSTR(pilot_name, ' ') - 1) AS часть_1,
  CASE WHEN INSTR(SUBSTR(pilot_name, INSTR(pilot_name, ' ') + 1), ' ') > 0
    THEN SUBSTR(SUBSTR(pilot_name, INSTR(pilot_name, ' ') + 1), 1, INSTR(SUBSTR(pilot_name, INSTR(pilot_name, ' ') + 1), ' ') - 1)
    ELSE SUBSTR(pilot_name, INSTR(pilot_name, ' ') + 1) END AS часть_2,
  CASE WHEN INSTR(SUBSTR(pilot_name, INSTR(pilot_name, ' ') + 1), ' ') > 0
    THEN SUBSTR(SUBSTR(pilot_name, INSTR(pilot_name, ' ') + 1), INSTR(SUBSTR(pilot_name, INSTR(pilot_name, ' ') + 1), ' ') + 1)
    ELSE NULL END AS часть_3
FROM flights
ORDER BY flight_number
LIMIT 25;""",
        ),
    ]

    for title, comment, sql in tasks:
        _prn(output, "\n" + "=" * 60)
        _prn(output, title)
        _prn(output, "=" * 60)
        _prn(output, "Комментарий:", comment)
        _prn(output, "SQL (полный запрос):")
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
