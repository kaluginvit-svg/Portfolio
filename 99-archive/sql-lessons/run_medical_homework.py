# -*- coding: utf-8 -*-
"""
Скрипт выполняет SQL-запросы по медицинским данным (medical_data_reduced.csv).
Загружает CSV в SQLite, выполняет задания и выводит результаты в medical_homework_results.txt.
"""
import sqlite3
import csv
import os

# Путь к файлу базы данных SQLite (создаётся при запуске)
DB_PATH = "medical_homework.db"
# Путь к CSV с медицинскими данными (PatientID, Age, Weight, Height, Gender, Condition, SystolicBP)
CSV_PATH = "medical_data_reduced.csv"
# Файл, в который записываются результаты (аналогично homework_results.txt)
OUTPUT_PATH = "medical_homework_results.txt"


def _prn(output, *a, **k):
    """Печать в переданный поток (файл или консоль)."""
    print(*a, **k, file=output)


def _format_table(output, cur):
    """
    Форматирует результат последнего запроса в виде таблицы и выводит в output.
    Возвращает количество выведенных строк.
    """
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

    # Подключение к SQLite и создание таблицы medical
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS medical")
    # Таблица: PatientID, Age (лет), Weight (кг), Height (см), Gender, Condition, SystolicBP (мм рт. ст.)
    conn.execute("""
        CREATE TABLE medical (
            PatientID INTEGER,
            Age INTEGER,
            Weight REAL,
            Height REAL,
            Gender TEXT,
            Condition TEXT,
            SystolicBP REAL
        )
    """)

    # Загрузка данных из CSV (пустые поля сохраняем как NULL)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, CSV_PATH)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get("PatientID", "").strip()
            age = row.get("Age", "").strip()
            weight = row.get("Weight", "").strip()
            height = row.get("Height", "").strip()
            gender = row.get("Gender", "").strip() or None
            condition = row.get("Condition", "").strip() or None
            sbp = row.get("SystolicBP", "").strip()
            pid = int(pid) if pid else None
            age = int(age) if age else None
            weight = float(weight) if weight else None
            height = float(height) if height else None
            sbp = float(sbp) if sbp else None
            conn.execute(
                "INSERT INTO medical (PatientID, Age, Weight, Height, Gender, Condition, SystolicBP) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (pid, age, weight, height, gender, condition, sbp),
            )
    conn.commit()
    cur = conn.cursor()

    # Заголовок отчёта (как в homework_results.txt)
    _prn(output, "ДОМАШНЕЕ ЗАДАНИЕ: РЕЗУЛЬТАТЫ SQL-ЗАПРОСОВ ПО МЕДИЦИНСКИМ ДАННЫМ")
    _prn(output, "Источник данных: medical_data_reduced.csv → таблица medical(PatientID, Age, Weight, Height, Gender, Condition, SystolicBP).")
    _prn(output, "Рост в см, вес в кг, давление — систолическое в мм рт. ст.")
    _prn(output, "")

    # Список заданий: (заголовок, комментарий, SQL-запрос)
    tasks = [
        (
            "1. Разница между ростом и весом для каждого пациента (арифметические операторы)",
            "Действие: вычисляем разницу Height - Weight для каждой записи (рост и вес в разных единицах; разница для наглядности арифметики).",
            "SELECT PatientID, Height, Weight, ROUND(Height - Weight, 2) AS Height_minus_Weight FROM medical",
        ),
        (
            "2. Общее количество записей (пока без группировки)",
            "Действие: подсчёт общего числа строк в таблице с помощью COUNT(*).",
            "SELECT COUNT(*) AS total_records FROM medical",
        ),
        (
            "3. Возраст пациента в днях (в году 365 дней)",
            "Действие: возраст в годах умножаем на 365 — получаем возраст в днях для каждого пациента.",
            "SELECT PatientID, Age AS Age_years, (Age * 365) AS Age_days FROM medical",
        ),
        (
            "4. Средний рост пациентов",
            "Действие: агрегатная функция AVG(Height) — среднее значение роста по всем записям.",
            "SELECT AVG(Height) AS avg_height FROM medical",
        ),
        (
            "5. Минимальный и максимальный вес пациентов",
            "Действие: агрегатные функции MIN(Weight) и MAX(Weight).",
            "SELECT MIN(Weight) AS min_weight, MAX(Weight) AS max_weight FROM medical",
        ),
        (
            "6. Количество уникальных пациентов",
            "Действие: подсчёт уникальных значений PatientID с помощью COUNT(DISTINCT PatientID).",
            "SELECT COUNT(DISTINCT PatientID) AS unique_patients FROM medical",
        ),
        (
            "7. Уникальные заболевания (столбец Condition)",
            "Действие: выводим все уникальные значения столбца Condition через DISTINCT.",
            "SELECT DISTINCT Condition FROM medical ORDER BY Condition",
        ),
        (
            "8. Средний рост, мин и макс вес по полу (GROUP BY Gender)",
            "Действие: группировка по полю Gender; для каждой группы — AVG(Height), MIN(Weight), MAX(Weight).",
            "SELECT Gender, AVG(Height) AS avg_height, MIN(Weight) AS min_weight, MAX(Weight) AS max_weight FROM medical GROUP BY Gender",
        ),
        (
            "9. Индекс массы тела (ИМТ) для каждого пациента (необязательное)",
            "Действие: ИМТ = вес (кг) / (рост (м))^2; рост в таблице в см, переводим в метры: Height/100.",
            "SELECT PatientID, Weight, Height, ROUND(Weight / ((Height/100.0) * (Height/100.0)), 2) AS BMI FROM medical",
        ),
        (
            "10. Пациенты с ростом и весом выше среднего по своему полу (один запрос)",
            "Действие: для каждого пола (Male/Female) в подзапросах считаем средний рост и вес; в основном запросе WHERE отбираем тех, у кого рост и вес выше этих средних.",
            """SELECT PatientID, Gender, Height, Weight
FROM medical m
WHERE m.Gender IS NOT NULL
  AND (
    (m.Gender = 'Male' AND m.Height > (SELECT AVG(Height) FROM medical WHERE Gender = 'Male') AND m.Weight > (SELECT AVG(Weight) FROM medical WHERE Gender = 'Male'))
    OR
    (m.Gender = 'Female' AND m.Height > (SELECT AVG(Height) FROM medical WHERE Gender = 'Female') AND m.Weight > (SELECT AVG(Weight) FROM medical WHERE Gender = 'Female'))
  )
ORDER BY m.Gender, m.PatientID""",
        ),
        (
            "11. Кровяное давление: из мм рт. ст. в паскали",
            "Действие: перевод SystolicBP из mmHg в Па по формуле: 1 мм рт. ст. = 133.322 Па.",
            "SELECT PatientID, SystolicBP AS SystolicBP_mmHg, ROUND(SystolicBP * 133.322, 2) AS SystolicBP_Pa FROM medical",
        ),
    ]

    for title, comment, sql in tasks:
        _prn(output, "\n" + "=" * 60)
        _prn(output, title)
        _prn(output, "=" * 60)
        _prn(output, "Комментарий:", comment)
        _prn(output, "SQL:", sql.strip()[:80] + ("..." if len(sql.strip()) > 80 else ""))
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
