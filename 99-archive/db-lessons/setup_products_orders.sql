-- ============================================================
-- СОЗДАНИЕ ТАБЛИЦ PRODUCTS И ORDERS
-- ============================================================
-- Этот скрипт создает таблицы и заполняет их данными
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- ТАБЛИЦА ТОВАРОВ (PRODUCTS)
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,              -- Артикул товара (SKU)
    name TEXT NOT NULL,                    -- Название товара
    category TEXT NOT NULL,                -- Категория товара
    description TEXT,                      -- Описание товара
    price REAL NOT NULL CHECK(price > 0),  -- Цена товара
    stock_quantity INTEGER DEFAULT 0,      -- Количество на складе
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ТАБЛИЦА ЗАКАЗОВ (ORDERS)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,     -- Номер заказа
    customer_name TEXT NOT NULL,           -- Имя клиента
    customer_email TEXT,                   -- Email клиента
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    status TEXT NOT NULL DEFAULT 'Новый' CHECK(status IN ('Новый', 'Оплачен', 'Отменен', 'Доставлен'))
);

-- ============================================================
-- ТАБЛИЦА ПОЗИЦИЙ ЗАКАЗА (ORDER_ITEMS)
-- ============================================================
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price REAL NOT NULL CHECK(price > 0),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- ============================================================
-- ИНДЕКСЫ ДЛЯ УСКОРЕНИЯ ПОИСКА
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- ============================================================
-- МАССОВАЯ ВСТАВКА ТОВАРОВ (≥100 товаров)
-- ============================================================
-- Используем рекурсивный CTE для генерации 120 товаров

INSERT INTO products (sku, name, category, description, price, stock_quantity)
WITH RECURSIVE generate_products(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1
    FROM generate_products
    WHERE n < 120
)
SELECT 
    -- Генерация SKU: SKU-XXXXX (5 цифр)
    'SKU-' || printf('%05d', abs(random() % 100000)) || '-' || n AS sku,
    
    -- Генерация названия товара
    CASE (abs(random() % 12))
        WHEN 0 THEN 'Смартфон ' || (abs(random() % 50) + 1)
        WHEN 1 THEN 'Ноутбук ' || (abs(random() % 30) + 1)
        WHEN 2 THEN 'Планшет ' || (abs(random() % 20) + 1)
        WHEN 3 THEN 'Наушники ' || (abs(random() % 40) + 1)
        WHEN 4 THEN 'Клавиатура ' || (abs(random() % 25) + 1)
        WHEN 5 THEN 'Мышь ' || (abs(random() % 35) + 1)
        WHEN 6 THEN 'Монитор ' || (abs(random() % 15) + 1)
        WHEN 7 THEN 'Принтер ' || (abs(random() % 20) + 1)
        WHEN 8 THEN 'Камера ' || (abs(random() % 18) + 1)
        WHEN 9 THEN 'Колонки ' || (abs(random() % 22) + 1)
        WHEN 10 THEN 'Роутер ' || (abs(random() % 16) + 1)
        ELSE 'Планшет ' || (abs(random() % 22) + 1)
    END AS name,
    
    -- Генерация категории
    CASE (abs(random() % 6))
        WHEN 0 THEN 'Электроника'
        WHEN 1 THEN 'Компьютеры'
        WHEN 2 THEN 'Аксессуары'
        WHEN 3 THEN 'Периферия'
        WHEN 4 THEN 'Гаджеты'
        ELSE 'Офисная техника'
    END AS category,
    
    -- Генерация описания
    'Описание товара #' || n || '. Качественный продукт с отличными характеристиками. ' ||
    CASE (abs(random() % 3))
        WHEN 0 THEN 'Рекомендуется для профессионального использования.'
        WHEN 1 THEN 'Идеально подходит для дома и офиса.'
        ELSE 'Проверенное качество и надежность.'
    END AS description,
    
    -- Генерация цены: от 500 до 50000 рублей
    round((abs(random() % 49500) + 500) + (abs(random() % 100) / 100.0), 2) AS price,
    
    -- Генерация количества на складе: от 0 до 100
    abs(random() % 101) AS stock_quantity

FROM generate_products;

-- ============================================================
-- ПРОВЕРКА СОЗДАННЫХ ДАННЫХ
-- ============================================================
SELECT 'Товары созданы:' AS info;
SELECT COUNT(*) AS total_products FROM products;

SELECT 'Статистика по категориям:' AS info;
SELECT 
    category,
    COUNT(*) AS count,
    round(AVG(price), 2) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM products
GROUP BY category
ORDER BY count DESC;
