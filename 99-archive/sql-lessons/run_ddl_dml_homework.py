# -*- coding: utf-8 -*-
"""
Домашнее задание: команды DDL и DML.
Создание/изменение таблиц и индексов, вставка, обновление, удаление данных.
Итог — ddl_dml_homework_results.txt с полным SQL по каждому шагу и результатами.
"""
import sqlite3
import os

DB_PATH = "ddl_dml_homework.db"
OUTPUT_PATH = "ddl_dml_homework_results.txt"


def _prn(output, *a, **k):
    print(*a, **k, file=output)


def _format_table(output, cur):
    rows = cur.fetchall()
    if not cur.description:
        _prn(output, "(нет выборки)")
        return
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


def main(output=None):
    if output is None:
        output = __import__("sys").stdout

    script_dir = os.path.dirname(os.path.abspath(__file__)) or "."
    db_path = os.path.join(script_dir, DB_PATH)
    if os.path.isfile(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    _prn(output, "ДОМАШНЕЕ ЗАДАНИЕ: КОМАНДЫ DDL И DML")
    _prn(output, "Урок: создание/изменение таблиц и индексов, вставка, обновление, удаление данных.")
    _prn(output, "")

    steps = [
        ("1. Создать таблицу «projects»: project_id (INT, PK), project (TEXT), start_date (DATE), end_date (DATE)",
         """CREATE TABLE projects (
  project_id INTEGER PRIMARY KEY,
  project TEXT,
  start_date DATE,
  end_date DATE
);""",
         None),
        ("2. Создать таблицу «tasks»: task_id (INT, PK), task_name (TEXT), project_id (INT, FK → projects)",
         """CREATE TABLE tasks (
  task_id INTEGER PRIMARY KEY,
  task_name TEXT,
  project_id INTEGER,
  FOREIGN KEY (project_id) REFERENCES projects(project_id)
);""",
         None),
        ("3. Переименовать столбец project в project_name в таблице «projects»",
         "ALTER TABLE projects RENAME COLUMN project TO project_name;",
         None),
        ("4. Создать индекс inx_projects_project_name на project_name",
         "CREATE INDEX inx_projects_project_name ON projects(project_name);",
         None),
        ("5. Создать индекс inx_tasks_project_id на project_id",
         "CREATE INDEX inx_tasks_project_id ON tasks(project_id);",
         None),
        ("6. Удалить индекс inx_tasks_project_id",
         "DROP INDEX IF EXISTS inx_tasks_project_id;",
         None),
        ("7. Удалить индекс inx_projects_project_name",
         "DROP INDEX IF EXISTS inx_projects_project_name;",
         None),
        ("8. Вставить строку в «projects»: project_name='Project Alpha', start_date='2024-01-01'",
         "INSERT INTO projects (project_name, start_date) VALUES ('Project Alpha', '2024-01-01');",
         "SELECT * FROM projects;"),
        ("9. Вставить строку в «tasks»: task_name='Task 1', project_id=1",
         "INSERT INTO tasks (task_name, project_id) VALUES ('Task 1', 1);",
         "SELECT * FROM tasks;"),
        ("10. Обновить start_date для project_id=1 на 2024-02-01",
         "UPDATE projects SET start_date = '2024-02-01' WHERE project_id = 1;",
         "SELECT * FROM projects;"),
        ("11. Обновить task_name для task_id=1 на «Initial Task»",
         "UPDATE tasks SET task_name = 'Initial Task' WHERE task_id = 1;",
         "SELECT * FROM tasks;"),
        ("12. Удалить строку с project_id=1 из «projects»",
         "DELETE FROM projects WHERE project_id = 1;",
         "SELECT * FROM projects;"),
        ("13. Удалить строку с task_id=1 из «tasks»",
         "DELETE FROM tasks WHERE task_id = 1;",
         "SELECT * FROM tasks;"),
        ("14. Вставить project_id=2, project_name='Project Beta', start_date='2024-03-01'; при конфликте обновить project_name",
         """INSERT INTO projects (project_id, project_name, start_date)
VALUES (2, 'Project Beta', '2024-03-01')
ON CONFLICT(project_id) DO UPDATE SET project_name = 'Project Beta';""",
         "SELECT * FROM projects;"),
        ("15. Вставить task_id=2, task_name='Task 2', project_id=1; при конфликте обновить task_name",
         """INSERT INTO tasks (task_id, task_name, project_id)
VALUES (2, 'Task 2', 1)
ON CONFLICT(task_id) DO UPDATE SET task_name = 'Task 2';""",
         "SELECT * FROM tasks;"),
        ("16. Вставить project_name='Project Gamma', start_date='2024-04-01' и вернуть все столбцы после вставки",
         """INSERT INTO projects (project_name, start_date)
VALUES ('Project Gamma', '2024-04-01')
RETURNING *;""",
         "RETURNING"),  # результат уже в последнем execute
        ("17. Вставить задачу task_name='Design Database Schema', project_id=1 и вернуть все столбцы",
         """INSERT INTO tasks (task_name, project_id)
VALUES ('Design Database Schema', 1)
RETURNING *;""",
         "RETURNING"),
        ("18. Удалить столбец project_id из таблицы «tasks» (пересоздание таблицы без столбца и FK)",
         ("CREATE TABLE tasks_new (task_id INTEGER PRIMARY KEY, task_name TEXT);",
          "INSERT INTO tasks_new (task_id, task_name) SELECT task_id, task_name FROM tasks;",
          "DROP TABLE tasks;",
          "ALTER TABLE tasks_new RENAME TO tasks;"),
         "SELECT * FROM tasks LIMIT 5;"),
        ("19. Удалить таблицу «projects»",
         "DROP TABLE projects;",
         None),
        ("20. Удалить таблицу «tasks»",
         "DROP TABLE tasks;",
         None),
    ]

    for title, sql, select_after in steps:
        _prn(output, "\n" + "=" * 60)
        _prn(output, title)
        _prn(output, "=" * 60)
        _prn(output, "SQL (полная команда):")
        if isinstance(sql, tuple):
            for s in sql:
                _prn(output, s.strip())
            _prn(output, "")
            for s in sql:
                cur.execute(s)
        else:
            _prn(output, sql.strip())
            _prn(output, "")
            cur.execute(sql)
        if select_after == "RETURNING":
            rows = cur.fetchall()
            conn.commit()
            if cur.description and rows:
                _prn(output, "Результат (RETURNING *):")
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
        else:
            conn.commit()
            if select_after:
                cur.execute(select_after)
                _prn(output, "Результат выборки:")
                _format_table(output, cur)
            else:
                _prn(output, "Выполнено.")

    conn.close()
    _prn(output, "\nГотово.")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__)) or "."
    out_path = os.path.join(script_dir, OUTPUT_PATH)
    with open(out_path, "w", encoding="utf-8") as f:
        main(f)
    print("Результаты сохранены в", out_path)
