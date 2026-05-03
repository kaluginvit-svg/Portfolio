-- ============================================================
-- СОЗДАНИЕ СВЯЗАННЫХ ТАБЛИЦ ДЛЯ ИЗУЧЕНИЯ JOIN
-- ============================================================
-- Этот скрипт создает таблицы orders и order_items,
-- которые связаны с таблицей products через внешние ключи
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- ТАБЛИЦА ЗАКАЗОВ
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    status TEXT NOT NULL DEFAULT 'Новый' CHECK(status IN ('Новый', 'Оплачен', 'Отменен', 'Доставлен'))
);

-- ============================================================
-- ТАБЛИЦА ПОЗИЦИЙ ЗАКАЗА (связь many-to-many между orders и products)
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
-- ИНДЕКСЫ ДЛЯ УСКОРЕНИЯ JOIN
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);

-- ============================================================
-- ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ
-- ============================================================

-- Вставляем заказы
INSERT INTO orders (order_number, customer_name, customer_email, total_amount, status) VALUES
('ORD-001', 'Иван Иванов', 'ivan@example.com', 45000.50, 'Оплачен'),
('ORD-002', 'Мария Петрова', 'maria@example.com', 25000.00, 'Новый'),
('ORD-003', 'Александр Сидоров', 'alex@example.com', 15000.75, 'Оплачен'),
('ORD-004', 'Елена Козлова', 'elena@example.com', 35000.00, 'Доставлен'),
('ORD-005', 'Дмитрий Смирнов', 'dmitry@example.com', 12000.50, 'Новый'),
('ORD-006', 'Ольга Волкова', 'olga@example.com', 28000.25, 'Оплачен'),
('ORD-007', 'Сергей Новиков', 'sergey@example.com', 55000.00, 'Оплачен'),
('ORD-008', 'Анна Лебедева', 'anna@example.com', 18000.75, 'Новый');

-- Вставляем позиции заказов
-- Заказ 1 (ORD-001)
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 2, 15000.50),  -- 2x Смартфон
(1, 2, 1, 15000.00);  -- 1x Ноутбук

-- Заказ 2 (ORD-002)
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(2, 3, 1, 25000.00);  -- 1x Планшет

-- Заказ 3 (ORD-003)
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(3, 1, 1, 15000.75);  -- 1x Смартфон

-- Заказ 4 (ORD-004)
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(4, 2, 1, 35000.00);  -- 1x Ноутбук

-- Заказ 5 (ORD-005)
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(5, 4, 2, 6000.25);   -- 2x Наушники

-- Заказ 6 (ORD-006)
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(6, 5, 1, 15000.00),  -- 1x Клавиатура
(6, 6, 1, 13000.25);  -- 1x Мышь

-- Заказ 7 (ORD-007)
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(7, 2, 1, 35000.00),  -- 1x Ноутбук
(7, 7, 1, 20000.00);  -- 1x Монитор

-- Заказ 8 (ORD-008)
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(8, 1, 1, 15000.75),  -- 1x Смартфон
(8, 8, 1, 3000.00);   -- 1x Принтер

-- ============================================================
-- ПРОВЕРКА СОЗДАННЫХ ДАННЫХ
-- ============================================================
SELECT 'Заказы:' AS info;
SELECT COUNT(*) AS total_orders FROM orders;

SELECT 'Позиции заказов:' AS info;
SELECT COUNT(*) AS total_items FROM order_items;

SELECT 'Примеры заказов:' AS info;
SELECT * FROM orders LIMIT 5;

SELECT 'Примеры позиций:' AS info;
SELECT * FROM order_items LIMIT 5;
