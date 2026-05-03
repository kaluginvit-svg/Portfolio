-- ============================================================
-- ГЕНЕРАЦИЯ 1000 СЛУЧАЙНЫХ ТОВАРОВ
-- ============================================================
-- Этот скрипт создает таблицу products и заполняет её
-- 1000 случайными записями с использованием INSERT ... SELECT
-- ============================================================

-- Создание таблицы products (если не существует)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article TEXT NOT NULL UNIQUE,           -- Артикул товара
    name TEXT NOT NULL,                     -- Название товара
    description TEXT,                       -- Описание товара
    category TEXT NOT NULL,                 -- Категория товара
    price REAL NOT NULL CHECK(price > 0),  -- Цена товара
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ВСТАВКА 1000 СЛУЧАЙНЫХ ЗАПИСЕЙ
-- ============================================================
-- Используем INSERT ... SELECT с рекурсивным CTE для генерации
-- ============================================================

INSERT INTO products (article, name, description, category, price)
WITH RECURSIVE generate_products(n) AS (
    -- Базовый случай: начинаем с 1
    SELECT 1
    UNION ALL
    -- Рекурсивный случай: увеличиваем n до 1000
    SELECT n + 1 FROM generate_products WHERE n < 1000
),
categories AS (
    SELECT 'Электроника' AS cat UNION ALL
    SELECT 'Одежда' UNION ALL
    SELECT 'Обувь' UNION ALL
    SELECT 'Мебель' UNION ALL
    SELECT 'Книги' UNION ALL
    SELECT 'Спорт' UNION ALL
    SELECT 'Игрушки' UNION ALL
    SELECT 'Красота' UNION ALL
    SELECT 'Еда' UNION ALL
    SELECT 'Авто'
),
names AS (
    SELECT 'Профессиональный' AS prefix UNION ALL
    SELECT 'Премиум' UNION ALL
    SELECT 'Стандартный' UNION ALL
    SELECT 'Экономичный' UNION ALL
    SELECT 'Улучшенный' UNION ALL
    SELECT 'Классический' UNION ALL
    SELECT 'Современный' UNION ALL
    SELECT 'Универсальный'
),
suffixes AS (
    SELECT 'устройство' AS suffix UNION ALL
    SELECT 'прибор' UNION ALL
    SELECT 'аксессуар' UNION ALL
    SELECT 'комплект' UNION ALL
    SELECT 'набор' UNION ALL
    SELECT 'модель' UNION ALL
    SELECT 'версия'
)
SELECT 
    -- Генерация артикула: ART-XXXXXX (6 случайных цифр)
    'ART-' || printf('%06d', abs(random()) % 1000000) || '-' || n AS article,
    
    -- Генерация названия: случайный префикс + категория + случайный суффикс
    (SELECT prefix FROM names ORDER BY random() LIMIT 1) || ' ' ||
    (SELECT cat FROM categories ORDER BY random() LIMIT 1) || ' ' ||
    (SELECT suffix FROM suffixes ORDER BY random() LIMIT 1) AS name,
    
    -- Генерация описания
    'Качественный товар категории ' || 
    (SELECT cat FROM categories ORDER BY random() LIMIT 1) || 
    '. Идеально подходит для повседневного использования. ' ||
    CASE abs(random()) % 4
        WHEN 0 THEN 'Высокое качество материалов.'
        WHEN 1 THEN 'Современный дизайн и функциональность.'
        WHEN 2 THEN 'Проверенная временем надежность.'
        ELSE 'Оптимальное соотношение цены и качества.'
    END AS description,
    
    -- Случайная категория
    (SELECT cat FROM categories ORDER BY random() LIMIT 1) AS category,
    
    -- Случайная цена от 100 до 50000 рублей (округленная до 2 знаков)
    round(
        (abs(random()) % 49900 + 100) + 
        (abs(random()) % 100) / 100.0, 
        2
    ) AS price
    
FROM generate_products;

-- ============================================================
-- ПРОВЕРКА РЕЗУЛЬТАТА
-- ============================================================
SELECT 
    COUNT(*) AS total_products,
    COUNT(DISTINCT category) AS total_categories,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    round(AVG(price), 2) AS avg_price
FROM products;

-- Показать несколько примеров созданных товаров
SELECT article, name, category, price 
FROM products 
ORDER BY random() 
LIMIT 10;
