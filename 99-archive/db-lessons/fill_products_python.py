#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для заполнения таблицы products товарами
Используйте, если SQL рекурсивный CTE не работает в DBeaver
"""

import sqlite3
import random

db_path = 'products_orders.db'

# Подключение к базе данных
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Заполнение таблицы products товарами...")

# Категории товаров
categories = ['Электроника', 'Компьютеры', 'Аксессуары', 'Периферия', 'Гаджеты', 'Офисная техника']

# Типы товаров
product_types = [
    ('Смартфон', 'Электроника'),
    ('Ноутбук', 'Компьютеры'),
    ('Планшет', 'Электроника'),
    ('Наушники', 'Аксессуары'),
    ('Клавиатура', 'Периферия'),
    ('Мышь', 'Периферия'),
    ('Монитор', 'Периферия'),
    ('Принтер', 'Офисная техника'),
    ('Камера', 'Электроника'),
    ('Колонки', 'Аксессуары'),
    ('Роутер', 'Гаджеты'),
    ('Планшет', 'Электроника')
]

# Описания
descriptions = [
    'Рекомендуется для профессионального использования.',
    'Идеально подходит для дома и офиса.',
    'Проверенное качество и надежность.'
]

# Генерация 120 товаров
products_data = []
for i in range(1, 121):
    product_type, default_category = random.choice(product_types)
    category = random.choice(categories)
    sku = f'SKU-{random.randint(10000, 99999)}-{i}'
    name = f'{product_type} {random.randint(1, 50)}'
    description = f'Описание товара #{i}. Качественный продукт с отличными характеристиками. {random.choice(descriptions)}'
    price = round(random.uniform(500, 50000), 2)
    stock_quantity = random.randint(0, 100)
    
    products_data.append((sku, name, category, description, price, stock_quantity))

# Вставка данных
cursor.executemany('''
    INSERT INTO products (sku, name, category, description, price, stock_quantity)
    VALUES (?, ?, ?, ?, ?, ?)
''', products_data)

conn.commit()

# Проверка
cursor.execute('SELECT COUNT(*) FROM products')
count = cursor.fetchone()[0]
print(f"✓ Вставлено товаров: {count}")

# Статистика по категориям
cursor.execute('''
    SELECT category, COUNT(*) AS count, round(AVG(price), 2) AS avg_price
    FROM products
    GROUP BY category
    ORDER BY count DESC
''')
print("\nСтатистика по категориям:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} товаров, средняя цена: {row[2]}")

conn.close()
print("\n✓ Готово!")
