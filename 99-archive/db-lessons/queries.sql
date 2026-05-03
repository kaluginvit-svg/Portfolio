-- ============================================================
-- SQL ЗАПРОСЫ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
-- ============================================================
-- Базовые операции: INSERT, UPDATE, DELETE, SELECT
-- ============================================================

-- ============================================================
-- 1. INSERT - ВСТАВКА ДАННЫХ
-- ============================================================

-- 1.1. Ручная вставка товара #1
INSERT INTO products (sku, name, category, description, price, stock_quantity)
VALUES ('SKU-MANUAL-001', 'Премиум Смартфон Pro Max', 'Электроника', 
        'Флагманский смартфон с лучшими характеристиками на рынке. 256GB памяти, камера 108MP.', 
        89999.99, 15);

-- 1.2. Ручная вставка товара #2
INSERT INTO products (sku, name, category, description, price, stock_quantity)
VALUES ('SKU-MANUAL-002', 'Игровой Ноутбук RTX 4080', 'Компьютеры',
        'Мощный игровой ноутбук с видеокартой RTX 4080. 32GB RAM, SSD 1TB.',
        149999.00, 8);

-- 1.3. Ручная вставка товара #3
INSERT INTO products (sku, name, category, description, price, stock_quantity)
VALUES ('SKU-MANUAL-003', 'Беспроводные Наушники Premium', 'Аксессуары',
        'Высококачественные беспроводные наушники с шумоподавлением. Батарея 30 часов.',
        12999.50, 25);

-- 1.4. Массовая вставка товаров (добавляем еще 20 товаров)
INSERT INTO products (sku, name, category, description, price, stock_quantity)
SELECT 
    'SKU-BATCH-' || printf('%03d', n) AS sku,
    CASE (n % 5)
        WHEN 0 THEN 'Умные Часы ' || n
        WHEN 1 THEN 'Фитнес-браслет ' || n
        WHEN 2 THEN 'Power Bank ' || n
        WHEN 3 THEN 'Чехол для телефона ' || n
        ELSE 'Кабель USB-C ' || n
    END AS name,
    CASE (n % 3)
        WHEN 0 THEN 'Гаджеты'
        WHEN 1 THEN 'Аксессуары'
        ELSE 'Электроника'
    END AS category,
    'Описание товара из массовой вставки #' || n AS description,
    round((abs(random() % 10000) + 500) + (abs(random() % 100) / 100.0), 2) AS price,
    abs(random() % 50) AS stock_quantity
FROM (
    SELECT 121 + row_number() OVER () AS n
    FROM products
    LIMIT 20
);

-- ============================================================
-- 2. UPDATE - ОБНОВЛЕНИЕ ДАННЫХ
-- ============================================================

-- 2.1. Скидка 15% на все товары категории "Электроника"
UPDATE products
SET price = price * 0.85
WHERE category = 'Электроника';

-- Проверка результата
SELECT category, COUNT(*) AS count, round(AVG(price), 2) AS avg_price_after_discount
FROM products
WHERE category = 'Электроника'
GROUP BY category;

-- 2.2. Правка цены конкретного товара по SKU
UPDATE products
SET price = 79999.99,
    stock_quantity = 20,
    description = description || ' Цена обновлена. Акция!'
WHERE sku = 'SKU-MANUAL-001';

-- Проверка результата
SELECT sku, name, price, stock_quantity, description
FROM products
WHERE sku = 'SKU-MANUAL-001';

-- 2.3. Увеличение цены на 10% для товаров дороже 30000 рублей
UPDATE products
SET price = round(price * 1.1, 2)
WHERE price > 30000;

-- Проверка результата
SELECT 
    COUNT(*) AS updated_count,
    round(MIN(price), 2) AS min_price,
    round(MAX(price), 2) AS max_price,
    round(AVG(price), 2) AS avg_price
FROM products
WHERE price > 30000;

-- ============================================================
-- 3. DELETE - УДАЛЕНИЕ ДАННЫХ
-- ============================================================

-- 3.1. Безопасное удаление тестовых записей (товары с SKU начинающимся с SKU-BATCH-)
-- ВАЖНО: Сначала проверяем, что будет удалено!
SELECT COUNT(*) AS records_to_delete
FROM products
WHERE sku LIKE 'SKU-BATCH-%';

-- Удаление тестовых записей
DELETE FROM products
WHERE sku LIKE 'SKU-BATCH-%';

-- Проверка результата
SELECT COUNT(*) AS remaining_products FROM products;

-- ============================================================
-- 4. SELECT - ЧТЕНИЕ И АНАЛИЗ ДАННЫХ
-- ============================================================

-- 4.1. SELECT с WHERE + ORDER BY + LIMIT (Топ-10 самых дорогих товаров)
SELECT 
    sku,
    name,
    category,
    price,
    stock_quantity
FROM products
WHERE stock_quantity > 0  -- Только товары в наличии
ORDER BY price DESC
LIMIT 10;

-- 4.2. Агрегация: категории с количеством товаров и средней ценой
-- HAVING фильтрует группы с количеством товаров больше 5
SELECT 
    category,
    COUNT(*) AS product_count,
    round(AVG(price), 2) AS avg_price,
    round(MIN(price), 2) AS min_price,
    round(MAX(price), 2) AS max_price,
    SUM(stock_quantity) AS total_stock
FROM products
GROUP BY category
HAVING COUNT(*) > 5
ORDER BY product_count DESC;

-- 4.3. LIKE/поиск по шаблону: case-insensitive через UPPER()
-- Поиск товаров, название которых начинается с "СМАРТ" (независимо от регистра)
SELECT 
    sku,
    name,
    category,
    price
FROM products
WHERE UPPER(name) LIKE 'СМАРТ%'
ORDER BY price DESC;

-- Альтернативный вариант для кириллицы (учитывая особенности SQLite)
SELECT 
    sku,
    name,
    category,
    price
FROM products
WHERE name LIKE '%Смарт%' OR name LIKE '%смарт%' OR UPPER(name) LIKE '%СМАРТ%'
ORDER BY price DESC;

-- 4.4. JOIN: сводная выборка заказов с названием товара и суммой по категориям

-- Сначала создадим несколько тестовых заказов
INSERT INTO orders (order_number, customer_name, customer_email, total_amount, status) VALUES
('ORD-001', 'Иван Иванов', 'ivan@example.com', 45000.50, 'Оплачен'),
('ORD-002', 'Мария Петрова', 'maria@example.com', 25000.00, 'Новый'),
('ORD-003', 'Александр Сидоров', 'alex@example.com', 15000.75, 'Оплачен'),
('ORD-004', 'Елена Козлова', 'elena@example.com', 35000.00, 'Доставлен');

-- Добавим позиции в заказы
INSERT INTO order_items (order_id, product_id, quantity, price)
SELECT 
    1 AS order_id,
    id AS product_id,
    2 AS quantity,
    price
FROM products
WHERE category = 'Электроника'
LIMIT 2;

INSERT INTO order_items (order_id, product_id, quantity, price)
SELECT 
    2 AS order_id,
    id AS product_id,
    1 AS quantity,
    price
FROM products
WHERE category = 'Компьютеры'
LIMIT 1;

INSERT INTO order_items (order_id, product_id, quantity, price)
SELECT 
    3 AS order_id,
    id AS product_id,
    1 AS quantity,
    price
FROM products
WHERE category = 'Аксессуары'
LIMIT 1;

INSERT INTO order_items (order_id, product_id, quantity, price)
SELECT 
    4 AS order_id,
    id AS product_id,
    1 AS quantity,
    price
FROM products
WHERE category = 'Электроника'
LIMIT 1;

-- JOIN: Сводная выборка заказов с названием товара и суммой по категориям
SELECT 
    o.order_number,
    o.customer_name,
    o.order_date,
    o.status,
    p.name AS product_name,
    p.category,
    oi.quantity,
    oi.price AS item_price,
    (oi.quantity * oi.price) AS line_total
FROM orders o
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
ORDER BY o.order_date DESC, o.order_number;

-- Сумма по категориям в заказах
SELECT 
    p.category,
    COUNT(DISTINCT o.id) AS orders_count,
    COUNT(oi.id) AS items_count,
    SUM(oi.quantity) AS total_quantity,
    round(SUM(oi.quantity * oi.price), 2) AS total_revenue
FROM orders o
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- ============================================================
-- 5. БЕЗОПАСНОСТЬ: ПАРАМЕТРИЗАЦИЯ ЗАПРОСОВ
-- ============================================================

-- 5.1. НЕБЕЗОПАСНЫЙ ВАРИАНТ (SQL Injection уязвимость!)
-- ⚠️ РИСК: Злоумышленник может ввести вредоносный SQL код
-- Пример уязвимого Python кода:
-- 
-- user_input = "'; DROP TABLE products; --"
-- query = f"SELECT * FROM products WHERE name = '{user_input}'"
-- 
-- Результат: "SELECT * FROM products WHERE name = ''; DROP TABLE products; --'"
-- Это может удалить таблицу!

-- 5.2. БЕЗОПАСНЫЙ ВАРИАНТ (Параметризованный запрос)
-- ✅ БЕЗОПАСНО: Параметры передаются отдельно, SQL код не может быть изменен
-- Пример безопасного Python кода:
-- 
-- user_input = "'; DROP TABLE products; --"
-- query = "SELECT * FROM products WHERE name = ?"
-- cursor.execute(query, (user_input,))
-- 
-- Параметр '?' будет безопасно подставлен как обычное значение

-- Демонстрация безопасного запроса в SQL (для примера)
-- В реальном коде параметры передаются через API драйвера БД

-- Пример 1: Поиск по SKU (безопасно)
-- В Python: cursor.execute("SELECT * FROM products WHERE sku = ?", (sku_value,))
SELECT * FROM products WHERE sku = 'SKU-MANUAL-001';

-- Пример 2: Поиск по цене (безопасно)
-- В Python: cursor.execute("SELECT * FROM products WHERE price > ?", (min_price,))
SELECT * FROM products WHERE price > 10000;

-- Пример 3: Поиск по категории (безопасно)
-- В Python: cursor.execute("SELECT * FROM products WHERE category = ?", (category_name,))
SELECT * FROM products WHERE category = 'Электроника';

-- ============================================================
-- ДОПОЛНИТЕЛЬНЫЕ ПОЛЕЗНЫЕ ЗАПРОСЫ
-- ============================================================

-- Статистика по всем товарам
SELECT 
    COUNT(*) AS total_products,
    COUNT(DISTINCT category) AS categories_count,
    round(AVG(price), 2) AS avg_price,
    round(MIN(price), 2) AS min_price,
    round(MAX(price), 2) AS max_price,
    SUM(stock_quantity) AS total_stock
FROM products;

-- Товары с низким остатком на складе
SELECT 
    sku,
    name,
    category,
    stock_quantity,
    price
FROM products
WHERE stock_quantity < 10
ORDER BY stock_quantity ASC, price DESC;

-- Самые популярные категории (по количеству товаров)
SELECT 
    category,
    COUNT(*) AS product_count,
    round(AVG(price), 2) AS avg_price
FROM products
GROUP BY category
ORDER BY product_count DESC;
