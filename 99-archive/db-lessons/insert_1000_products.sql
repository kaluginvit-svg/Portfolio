-- ============================================================
-- ВСТАВКА 1000 СЛУЧАЙНЫХ ТОВАРОВ
-- ============================================================
-- Этот скрипт создает таблицу products и заполняет её
-- 1000 случайными записями с использованием рекурсивного CTE
-- ============================================================

-- Создание таблицы products (если не существует)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK(price > 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Очистка таблицы перед вставкой (опционально)
-- DELETE FROM products;

-- ============================================================
-- ВСТАВКА 1000 СЛУЧАЙНЫХ ТОВАРОВ
-- ============================================================
-- Используем рекурсивный CTE для генерации 1000 записей
-- ============================================================

INSERT INTO products (article, name, category, description, price)
WITH RECURSIVE generate_products(n) AS (
    -- Базовый случай: начинаем с 1
    SELECT 1
    
    UNION ALL
    
    -- Рекурсивный случай: увеличиваем n до 1000
    SELECT n + 1
    FROM generate_products
    WHERE n < 1000
)
SELECT 
    -- Генерация артикула: ART-XXXXX (5 случайных цифр)
    'ART-' || printf('%05d', abs(random() % 100000)) || '-' || n AS article,
    
    -- Генерация названия товара
    CASE (abs(random() % 10))
        WHEN 0 THEN 'Смартфон ' || (abs(random() % 50) + 1)
        WHEN 1 THEN 'Ноутбук ' || (abs(random() % 30) + 1)
        WHEN 2 THEN 'Планшет ' || (abs(random() % 20) + 1)
        WHEN 3 THEN 'Наушники ' || (abs(random() % 40) + 1)
        WHEN 4 THEN 'Клавиатура ' || (abs(random() % 25) + 1)
        WHEN 5 THEN 'Мышь ' || (abs(random() % 35) + 1)
        WHEN 6 THEN 'Монитор ' || (abs(random() % 15) + 1)
        WHEN 7 THEN 'Принтер ' || (abs(random() % 20) + 1)
        WHEN 8 THEN 'Камера ' || (abs(random() % 18) + 1)
        ELSE 'Планшет ' || (abs(random() % 22) + 1)
    END AS name,
    
    -- Генерация категории
    CASE (abs(random() % 5))
        WHEN 0 THEN 'Электроника'
        WHEN 1 THEN 'Компьютеры'
        WHEN 2 THEN 'Аксессуары'
        WHEN 3 THEN 'Периферия'
        ELSE 'Гаджеты'
    END AS category,
    
    -- Генерация описания
    'Описание товара #' || n || '. Качественный продукт с отличными характеристиками. ' ||
    CASE (abs(random() % 3))
        WHEN 0 THEN 'Рекомендуется для профессионального использования.'
        WHEN 1 THEN 'Идеально подходит для дома и офиса.'
        ELSE 'Проверенное качество и надежность.'
    END AS description,
    
    -- Генерация цены: от 500 до 50000 рублей (округление до 2 знаков)
    round((abs(random() % 49500) + 500) + (abs(random() % 100) / 100.0), 2) AS price

FROM generate_products;

-- ============================================================
-- ПРОВЕРКА РЕЗУЛЬТАТА
-- ============================================================
SELECT 
    COUNT(*) AS total_products,
    COUNT(DISTINCT category) AS categories_count,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    round(AVG(price), 2) AS avg_price
FROM products;

-- Показать несколько примеров
SELECT * FROM products LIMIT 10;
