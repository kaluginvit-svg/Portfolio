#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания базы данных homework.db и заполнения данными
"""

import sqlite3
import os

# Получаем директорию, где находится скрипт
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
os.chdir(script_dir)

# Подключение к базе данных (создастся автоматически, если не существует)
db_path = os.path.join(script_dir, 'homework.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Создание базы данных homework.db...")

# Создание таблицы students
print("Создание таблицы students...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    age REAL,
    is_active BOOLEAN
)
''')

# Вставка данных студентов
print("Заполнение таблицы данными...")
students_data = [
    ('Иван', 'Иванов', 20.5, 1),
    ('Мария', 'Петрова', 19.0, 1),
    ('Александр', 'Сидоров', 21.0, 0),
    ('Елена', 'Козлова', 20.0, 1),
    ('Дмитрий', 'Смирнов', 22.5, 1)
]

cursor.executemany('''
INSERT INTO students (first_name, last_name, age, is_active) 
VALUES (?, ?, ?, ?)
''', students_data)

# Сохранение изменений
conn.commit()

# Проверка данных
print("\nПроверка созданных данных:")
cursor.execute('SELECT * FROM students')
rows = cursor.fetchall()
print(f"Всего записей: {len(rows)}")
for row in rows:
    print(f"ID: {row[0]}, Имя: {row[1]}, Фамилия: {row[2]}, Возраст: {row[3]}, Активен: {row[4]}")

# Закрытие соединения
conn.close()

print(f"\n✓ База данных {db_path} успешно создана и заполнена данными!")
