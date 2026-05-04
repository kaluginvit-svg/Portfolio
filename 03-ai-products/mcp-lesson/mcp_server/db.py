"""SQLite-хранилище каталога товаров."""

from __future__ import annotations

import random
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "products.db"

CATEGORIES = (
    "Электроника",
    "Книги",
    "Одежда",
    "Дом и сад",
    "Спорт",
    "Игрушки",
    "Продукты",
    "Красота",
)

ADJECTIVES = (
    "Умный",
    "Компактный",
    "Премиум",
    "Базовый",
    "Профессиональный",
    "Детский",
    "Эко",
    "Лёгкий",
)

NOUNS = (
    "ноутбук",
    "телефон",
    "наушники",
    "клавиатура",
    "монитор",
    "книга",
    "футболка",
    "кроссовки",
    "чайник",
    "ковёр",
    "мяч",
    "конструктор",
    "кофе",
    "крем",
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL
            )
            """
        )
        conn.commit()

    with get_connection() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM products").fetchone()
        if count == 0:
            _seed_products(conn, 100)
            conn.commit()


def _seed_products(conn: sqlite3.Connection, n: int) -> None:
    rng = random.Random(42)
    rows = []
    for i in range(1, n + 1):
        name = f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)} #{i}"
        category = rng.choice(CATEGORIES)
        price = round(rng.uniform(99.0, 99999.0), 2)
        rows.append((name, category, price))
    conn.executemany(
        "INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
        rows,
    )
