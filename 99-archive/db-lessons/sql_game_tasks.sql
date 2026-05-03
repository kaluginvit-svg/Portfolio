-- ============================================================
-- ЗАПОЛНЕНИЕ ЗАДАНИЙ ДЛЯ SQL ИГРЫ
-- ============================================================

-- Уровень 1: Базовые SELECT запросы
INSERT INTO tasks (level, title, description, hint, sql_example, expected_columns, category, points) VALUES
(1, 'Выбери все товары', 
 'Напиши запрос, который выберет все товары из таблицы products. Используй SELECT *',
 'SELECT * FROM products;',
 'SELECT * FROM products;',
 'id,sku,name,category,description,price,stock_quantity,created_at',
 'SELECT', 10),

(1, 'Выбери названия и цены',
 'Выбери только названия (name) и цены (price) всех товаров',
 'SELECT name, price FROM products;',
 'SELECT name, price FROM products;',
 'name,price',
 'SELECT', 10),

(1, 'Сколько товаров?',
 'Посчитай общее количество товаров в таблице products',
 'SELECT COUNT(*) FROM products;',
 'SELECT COUNT(*) FROM products;',
 'COUNT(*)',
 'SELECT', 15),

-- Уровень 2: WHERE и фильтрация
(2, 'Товары дороже 10000',
 'Найди все товары, цена которых больше 10000 рублей',
 'SELECT * FROM products WHERE price > 10000;',
 'SELECT * FROM products WHERE price > 10000;',
 'id,sku,name,category,description,price,stock_quantity,created_at',
 'WHERE', 15),

(2, 'Товары категории Электроника',
 'Выбери все товары категории "Электроника"',
 'SELECT * FROM products WHERE category = ''Электроника'';',
 'SELECT * FROM products WHERE category = ''Электроника'';',
 'id,sku,name,category,description,price,stock_quantity,created_at',
 'WHERE', 15),

(2, 'Товары в наличии',
 'Найди товары, у которых stock_quantity больше 0 (есть на складе)',
 'SELECT * FROM products WHERE stock_quantity > 0;',
 'SELECT * FROM products WHERE stock_quantity > 0;',
 'id,sku,name,category,description,price,stock_quantity,created_at',
 'WHERE', 15),

(2, 'Поиск по названию',
 'Найди все товары, в названии которых есть слово "Смартфон"',
 'SELECT * FROM products WHERE name LIKE ''%Смартфон%'';',
 'SELECT * FROM products WHERE name LIKE ''%Смартфон%'';',
 'id,sku,name,category,description,price,stock_quantity,created_at',
 'LIKE', 20),

-- Уровень 3: Сортировка и ограничение
(3, 'Топ-10 самых дорогих',
 'Выбери 10 самых дорогих товаров, отсортированных по цене (от большей к меньшей)',
 'SELECT name, price FROM products ORDER BY price DESC LIMIT 10;',
 'SELECT name, price FROM products ORDER BY price DESC LIMIT 10;',
 'name,price',
 'ORDER_BY', 20),

(3, 'Самые дешевые товары',
 'Найди 5 самых дешевых товаров',
 'SELECT name, price FROM products ORDER BY price ASC LIMIT 5;',
 'SELECT name, price FROM products ORDER BY price ASC LIMIT 5;',
 'name,price',
 'ORDER_BY', 20),

(3, 'Товары в диапазоне цен',
 'Найди товары с ценой от 5000 до 15000 рублей',
 'SELECT * FROM products WHERE price BETWEEN 5000 AND 15000;',
 'SELECT * FROM products WHERE price BETWEEN 5000 AND 15000;',
 'id,sku,name,category,description,price,stock_quantity,created_at',
 'WHERE', 20),

-- Уровень 4: Агрегация и группировка
(4, 'Средняя цена по категориям',
 'Посчитай среднюю цену товаров в каждой категории',
 'SELECT category, AVG(price) FROM products GROUP BY category;',
 'SELECT category, AVG(price) FROM products GROUP BY category;',
 'category,AVG(price)',
 'GROUP_BY', 25),

(4, 'Количество товаров по категориям',
 'Посчитай количество товаров в каждой категории',
 'SELECT category, COUNT(*) FROM products GROUP BY category;',
 'SELECT category, COUNT(*) FROM products GROUP BY category;',
 'category,COUNT(*)',
 'GROUP_BY', 25),

(4, 'Категории с более чем 10 товарами',
 'Найди категории, в которых больше 10 товаров',
 'SELECT category, COUNT(*) FROM products GROUP BY category HAVING COUNT(*) > 10;',
 'SELECT category, COUNT(*) FROM products GROUP BY category HAVING COUNT(*) > 10;',
 'category,COUNT(*)',
 'HAVING', 30),

(4, 'Минимальная и максимальная цена',
 'Найди минимальную и максимальную цену товаров',
 'SELECT MIN(price), MAX(price) FROM products;',
 'SELECT MIN(price), MAX(price) FROM products;',
 'MIN(price),MAX(price)',
 'AGGREGATE', 25),

-- Уровень 5: JOIN и сложные запросы
(5, 'Товары в заказах',
 'Выбери все товары, которые есть в заказах. Используй JOIN между order_items и products',
 'SELECT p.name, p.category, oi.quantity FROM products p INNER JOIN order_items oi ON p.id = oi.product_id;',
 'SELECT p.name, p.category, oi.quantity FROM products p INNER JOIN order_items oi ON p.id = oi.product_id;',
 'name,category,quantity',
 'JOIN', 35),

(5, 'Заказы с товарами',
 'Выбери номер заказа, имя клиента и название товара. Используй JOIN между orders, order_items и products',
 'SELECT o.order_number, o.customer_name, p.name FROM orders o INNER JOIN order_items oi ON o.id = oi.order_id INNER JOIN products p ON oi.product_id = p.id;',
 'SELECT o.order_number, o.customer_name, p.name FROM orders o INNER JOIN order_items oi ON o.id = oi.order_id INNER JOIN products p ON oi.product_id = p.id;',
 'order_number,customer_name,name',
 'JOIN', 40),

(5, 'Сумма по категориям в заказах',
 'Посчитай общую сумму заказов по каждой категории товаров',
 'SELECT p.category, SUM(oi.quantity * oi.price) FROM products p INNER JOIN order_items oi ON p.id = oi.product_id GROUP BY p.category;',
 'SELECT p.category, SUM(oi.quantity * oi.price) FROM products p INNER JOIN order_items oi ON p.id = oi.product_id GROUP BY p.category;',
 'category,SUM(oi.quantity * oi.price)',
 'JOIN_GROUP', 45);
