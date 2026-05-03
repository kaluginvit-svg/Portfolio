-- ============================================================
-- СОЗДАНИЕ СТРУКТУРЫ ТАБЛИЦ
-- ============================================================
-- Этот скрипт создает таблицы products, orders и order_items
-- Без заполнения данными
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- ТАБЛИЦА ТОВАРОВ (PRODUCTS)
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,              -- Артикул товара (SKU - Stock Keeping Unit)
    name TEXT NOT NULL,                    -- Название товара
    category TEXT NOT NULL,                -- Категория товара
    description TEXT,                      -- Описание товара
    price REAL NOT NULL CHECK(price > 0),  -- Цена товара (должна быть больше 0)
    stock_quantity INTEGER DEFAULT 0,      -- Количество на складе
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- Дата создания записи
);

-- ============================================================
-- ТАБЛИЦА ЗАКАЗОВ (ORDERS)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,     -- Уникальный номер заказа
    customer_name TEXT NOT NULL,           -- Имя клиента
    customer_email TEXT,                   -- Email клиента
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Дата заказа
    total_amount REAL NOT NULL CHECK(total_amount >= 0),  -- Общая сумма заказа
    status TEXT NOT NULL DEFAULT 'Новый' CHECK(status IN ('Новый', 'Оплачен', 'Отменен', 'Доставлен'))  -- Статус заказа
);

-- ============================================================
-- ТАБЛИЦА ПОЗИЦИЙ ЗАКАЗА (ORDER_ITEMS)
-- ============================================================
-- Промежуточная таблица для связи many-to-many между orders и products
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,             -- Ссылка на заказ (внешний ключ)
    product_id INTEGER NOT NULL,           -- Ссылка на товар (внешний ключ)
    quantity INTEGER NOT NULL CHECK(quantity > 0),  -- Количество товара в заказе
    price REAL NOT NULL CHECK(price > 0),  -- Цена товара на момент заказа
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,  -- При удалении заказа удаляются позиции
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT  -- Запрет удаления товара, если он в заказе
);

-- ============================================================
-- ИНДЕКСЫ ДЛЯ УСКОРЕНИЯ ПОИСКА И JOIN
-- ============================================================

-- Индекс для быстрого поиска товаров по SKU
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);

-- Индекс для фильтрации по категориям
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

-- Индекс для поиска по цене (для сортировки и фильтрации)
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);

-- Индекс для поиска позиций по заказу (ускоряет JOIN)
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);

-- Индекс для поиска позиций по товару (ускоряет JOIN)
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- Индекс для фильтрации заказов по статусу
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- Индекс для сортировки заказов по дате
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);

-- Индекс для поиска заказов по номеру
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);

-- ============================================================
-- ПРОВЕРКА СОЗДАННЫХ ТАБЛИЦ
-- ============================================================

-- Показать список всех таблиц
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Показать структуру таблицы products (столбцы и их типы)
SELECT 
    name AS column_name,
    type AS data_type,
    CASE WHEN "notnull" = 1 THEN 'NOT NULL' ELSE '' END AS nullable,
    CASE WHEN dflt_value IS NOT NULL THEN 'DEFAULT ' || dflt_value ELSE '' END AS default_value,
    CASE WHEN pk = 1 THEN 'PRIMARY KEY' ELSE '' END AS primary_key
FROM pragma_table_info('products')
ORDER BY cid;

-- Показать структуру таблицы orders
SELECT 
    name AS column_name,
    type AS data_type,
    CASE WHEN "notnull" = 1 THEN 'NOT NULL' ELSE '' END AS nullable,
    CASE WHEN dflt_value IS NOT NULL THEN 'DEFAULT ' || dflt_value ELSE '' END AS default_value,
    CASE WHEN pk = 1 THEN 'PRIMARY KEY' ELSE '' END AS primary_key
FROM pragma_table_info('orders')
ORDER BY cid;

-- Показать структуру таблицы order_items
SELECT 
    name AS column_name,
    type AS data_type,
    CASE WHEN "notnull" = 1 THEN 'NOT NULL' ELSE '' END AS nullable,
    CASE WHEN dflt_value IS NOT NULL THEN 'DEFAULT ' || dflt_value ELSE '' END AS default_value,
    CASE WHEN pk = 1 THEN 'PRIMARY KEY' ELSE '' END AS primary_key
FROM pragma_table_info('order_items')
ORDER BY cid;

-- Показать внешние ключи таблицы order_items
SELECT 
    "from" AS column_name,
    "table" AS references_table,
    "to" AS references_column,
    on_delete,
    on_update
FROM pragma_foreign_key_list('order_items');

-- ============================================================
-- КОНЕЦ СКРИПТА СОЗДАНИЯ ТАБЛИЦ
-- ============================================================
