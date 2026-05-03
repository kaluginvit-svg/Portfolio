#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания таблиц products, orders и order_items
Можно использовать как альтернативу SQL файлу
"""

import sqlite3
import os

# Путь к базе данных
db_path = 'products_orders.db'

print("=" * 60)
print("СОЗДАНИЕ СТРУКТУРЫ ТАБЛИЦ")
print("=" * 60)

# Подключение к базе данных (создастся автоматически, если не существует)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Включаем поддержку внешних ключей
cursor.execute("PRAGMA foreign_keys = ON")
print("✓ Включена поддержка внешних ключей")

# ============================================================
# СОЗДАНИЕ ТАБЛИЦЫ PRODUCTS
# ============================================================
print("\n1. Создание таблицы products...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK(price > 0),
    stock_quantity INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
print("   ✓ Таблица products создана")

# ============================================================
# СОЗДАНИЕ ТАБЛИЦЫ ORDERS
# ============================================================
print("2. Создание таблицы orders...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    status TEXT NOT NULL DEFAULT 'Новый' CHECK(status IN ('Новый', 'Оплачен', 'Отменен', 'Доставлен'))
)
''')
print("   ✓ Таблица orders создана")

# ============================================================
# СОЗДАНИЕ ТАБЛИЦЫ ORDER_ITEMS
# ============================================================
print("3. Создание таблицы order_items...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price REAL NOT NULL CHECK(price > 0),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
)
''')
print("   ✓ Таблица order_items создана")

# ============================================================
# СОЗДАНИЕ ИНДЕКСОВ
# ============================================================
print("\n4. Создание индексов...")

indexes = [
    ("idx_products_sku", "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)"),
    ("idx_products_category", "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)"),
    ("idx_products_price", "CREATE INDEX IF NOT EXISTS idx_products_price ON products(price)"),
    ("idx_order_items_order_id", "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)"),
    ("idx_order_items_product_id", "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)"),
    ("idx_orders_status", "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)"),
    ("idx_orders_date", "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)"),
    ("idx_orders_order_number", "CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number)")
]

for index_name, index_sql in indexes:
    cursor.execute(index_sql)
    print(f"   ✓ Индекс {index_name} создан")

# Сохранение изменений
conn.commit()

# ============================================================
# ПРОВЕРКА СОЗДАННЫХ ТАБЛИЦ
# ============================================================
print("\n5. Проверка созданных таблиц...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print(f"   Найдено таблиц: {len(tables)}")
for table in tables:
    print(f"   - {table[0]}")

# Проверка структуры таблиц
print("\n6. Структура таблиц:")
for table_name in ['products', 'orders', 'order_items']:
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"\n   Таблица: {table_name}")
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        not_null = "NOT NULL" if col[3] else ""
        default = f"DEFAULT {col[4]}" if col[4] else ""
        pk = "PRIMARY KEY" if col[5] else ""
        print(f"     - {col_name} ({col_type}) {not_null} {default} {pk}".strip())

# Проверка внешних ключей
print("\n7. Проверка внешних ключей...")
cursor.execute("PRAGMA foreign_key_list(order_items)")
foreign_keys = cursor.fetchall()
if foreign_keys:
    print("   Внешние ключи в таблице order_items:")
    for fk in foreign_keys:
        print(f"     - {fk[3]} -> {fk[2]}.{fk[4]} (ON DELETE {fk[6]})")
else:
    print("   Внешние ключи не найдены")

conn.close()

print("\n" + "=" * 60)
print(f"✓ База данных {db_path} успешно создана!")
print("=" * 60)
print("\nСледующие шаги:")
print("1. Заполните таблицы данными (используйте setup_products_orders.sql)")
print("2. Выполните запросы из queries.sql")
