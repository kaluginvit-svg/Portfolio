# -*- coding: utf-8 -*-
"""
Создание базы данных recipes.db с таблицами для связи many-to-many
между продуктами и рецептами.

Запуск: python recipes.py
"""
import sqlite3
import os

# Путь к базе данных (создастся в текущей директории)
db_path = 'recipes.db'
print(f"Создание базы данных: {os.path.abspath(db_path)}")

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

# ============================================================
# СОЗДАНИЕ ТАБЛИЦ
# ============================================================
print("\n1. Создание таблиц...")

# Таблица продуктов
c.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)''')

# Таблица рецептов
c.execute('''CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    cooking_time INTEGER,
    servings INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)''')

# Промежуточная таблица для связи many-to-many
c.execute('''CREATE TABLE IF NOT EXISTS recipe_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(recipe_id, product_id)
)''')

# Индексы для ускорения поиска
c.execute('CREATE INDEX IF NOT EXISTS idx_recipe_id ON recipe_products(recipe_id)')
c.execute('CREATE INDEX IF NOT EXISTS idx_product_id ON recipe_products(product_id)')

# ============================================================
# ЗАПОЛНЕНИЕ ДАННЫМИ
# ============================================================
print("2. Заполнение данными...")

# Продукты
products = [
    ('Мука', 'г'), ('Сахар', 'г'), ('Яйца', 'шт'), ('Молоко', 'мл'),
    ('Масло сливочное', 'г'), ('Соль', 'г'), ('Дрожжи', 'г'),
    ('Помидоры', 'шт'), ('Лук', 'шт'), ('Чеснок', 'зубчик'),
    ('Морковь', 'шт'), ('Картофель', 'шт'), ('Мясо говяжье', 'г'),
    ('Перец черный', 'г'), ('Лавровый лист', 'шт'), ('Вода', 'мл'),
    ('Томатная паста', 'г'), ('Сметана', 'г'), ('Сыр', 'г'),
    ('Мука пшеничная', 'г')
]
c.executemany('INSERT INTO products (name, unit) VALUES (?, ?)', products)

# Рецепты
recipes = [
    ('Борщ', 'Классический украинский борщ с мясом и овощами', 120, 6),
    ('Оладьи', 'Пышные оладьи на молоке', 30, 4),
    ('Салат Оливье', 'Традиционный новогодний салат', 60, 8),
    ('Пицца Маргарита', 'Классическая итальянская пицца', 45, 4),
    ('Плов', 'Узбекский плов с мясом', 90, 6),
    ('Блины', 'Тонкие блины на молоке', 40, 6),
    ('Гуляш', 'Мясной гуляш с подливкой', 75, 5)
]
c.executemany('INSERT INTO recipes (name, description, cooking_time, servings) VALUES (?, ?, ?, ?)', recipes)

# Связи продукт-рецепт (recipe_id, product_id, quantity)
links = [
    # Борщ (1)
    (1, 13, 500), (1, 12, 300), (1, 11, 200), (1, 9, 2), (1, 10, 3),
    (1, 17, 50), (1, 15, 2), (1, 14, 5), (1, 6, 10), (1, 16, 2000),
    # Оладьи (2)
    (2, 1, 300), (2, 2, 50), (2, 3, 2), (2, 4, 250), (2, 5, 30), (2, 6, 5), (2, 7, 10),
    # Салат Оливье (3)
    (3, 12, 500), (3, 3, 4), (3, 11, 200), (3, 9, 1), (3, 18, 200), (3, 6, 10),
    # Пицца Маргарита (4)
    (4, 1, 500), (4, 7, 10), (4, 6, 10), (4, 16, 300), (4, 8, 400), (4, 19, 200), (4, 5, 50),
    # Плов (5)
    (5, 13, 600), (5, 9, 2), (5, 11, 200), (5, 6, 15), (5, 14, 5), (5, 16, 1000),
    # Блины (6)
    (6, 1, 200), (6, 3, 3), (6, 4, 500), (6, 2, 30), (6, 5, 50), (6, 6, 5),
    # Гуляш (7)
    (7, 13, 700), (7, 9, 2), (7, 11, 150), (7, 17, 100), (7, 6, 10), (7, 14, 5), (7, 16, 500)
]
c.executemany('INSERT INTO recipe_products (recipe_id, product_id, quantity) VALUES (?, ?, ?)', links)

conn.commit()

# ============================================================
# ПРОВЕРКА
# ============================================================
print("\n3. Проверка созданных данных:")
c.execute('SELECT COUNT(*) FROM products')
print(f"   Продуктов: {c.fetchone()[0]}")
c.execute('SELECT COUNT(*) FROM recipes')
print(f"   Рецептов: {c.fetchone()[0]}")
c.execute('SELECT COUNT(*) FROM recipe_products')
print(f"   Связей: {c.fetchone()[0]}")

# Пример: продукты в рецепте "Борщ"
print("\n4. Пример - продукты в рецепте 'Борщ':")
c.execute('''
    SELECT p.name, rp.quantity, p.unit
    FROM products p
    JOIN recipe_products rp ON p.id = rp.product_id
    JOIN recipes r ON rp.recipe_id = r.id
    WHERE r.name = 'Борщ'
    LIMIT 5
''')
for row in c.fetchall():
    print(f"   - {row[0]}: {row[1]} {row[2]}")

conn.close()
print(f"\n✓ База данных {db_path} успешно создана!")
