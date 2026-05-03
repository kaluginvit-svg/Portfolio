# SQL SELECT - Выборка данных из базы

## 📋 Содержание
1. [Обзор оператора SELECT](#обзор-оператора-select)
2. [Базовый синтаксис SELECT](#базовый-синтаксис-select)
3. [Выборка всех столбцов](#выборка-всех-столбцов)
4. [Выборка конкретных столбцов](#выборка-конкретных-столбцов)
5. [Фильтрация данных (WHERE)](#фильтрация-данных-where)
6. [Сортировка (ORDER BY)](#сортировка-order-by)
7. [Ограничение количества записей (LIMIT)](#ограничение-количества-записей-limit)
8. [Группировка (GROUP BY)](#группировка-group-by)
9. [Агрегатные функции](#агрегатные-функции)
10. [Условия для групп (HAVING)](#условия-для-групп-having)
11. [Уникальные значения (DISTINCT)](#уникальные-значения-distinct)
12. [Псевдонимы (ALIAS)](#псевдонимы-alias)
13. [Создание связанной таблицы](#создание-связанной-таблицы)
14. [JOIN - Соединение таблиц](#join---соединение-таблиц)
15. [Типы JOIN](#типы-join)
16. [Практические примеры](#практические-примеры)

---

## Обзор оператора SELECT

**SELECT** - это SQL-команда для выборки (чтения) данных из таблиц базы данных. Это один из самых часто используемых операторов в SQL.

### Что делает SELECT?

- Извлекает данные из одной или нескольких таблиц
- Фильтрует данные по условиям
- Сортирует результаты
- Группирует данные
- Выполняет вычисления и агрегации
- Объединяет данные из разных таблиц

### ⚠️ Важно!

**SELECT не изменяет данные!** Это операция только для чтения, она безопасна и не влияет на содержимое базы данных.

---

## Базовый синтаксис SELECT

```sql
SELECT column1, column2, ...
FROM table_name
WHERE condition
ORDER BY column
LIMIT number;
```

### Разбор синтаксиса:

- **`SELECT`** - ключевое слово, начинающее запрос на выборку
- **`column1, column2, ...`** - список столбцов для выборки
- **`FROM table_name`** - таблица, из которой выбираются данные
- **`WHERE condition`** - условие фильтрации (опционально)
- **`ORDER BY column`** - сортировка результатов (опционально)
- **`LIMIT number`** - ограничение количества записей (опционально)

---

## Выборка всех столбцов

### Пример 1: Выбрать все товары

```sql
SELECT * FROM products;
```

**Что происходит:**
- `*` - означает "все столбцы"
- Выбираются все записи из таблицы `products`
- Возвращаются все поля: id, article, name, category, description, price, created_at

**Результат:**
| id | article | name | category | description | price | created_at |
|----|---------|------|----------|-------------|-------|-------------|
| 1 | ART-12345-1 | Смартфон 25 | Электроника | Описание... | 15000.50 | 2024-01-01 |
| 2 | ART-67890-2 | Ноутбук 12 | Компьютеры | Описание... | 35000.75 | 2024-01-02 |

### ⚠️ Когда использовать `*`?

- ✅ Для быстрого просмотра данных
- ✅ Когда нужны все столбцы
- ❌ Избегайте в продакшене - лучше указывать конкретные столбцы для производительности

---

## Выборка конкретных столбцов

### Пример 2: Выбрать только название и цену

```sql
SELECT name, price FROM products;
```

**Что происходит:**
- Выбираются только столбцы `name` и `price`
- Порядок столбцов в SELECT определяет порядок в результате

**Результат:**
| name | price |
|------|-------|
| Смартфон 25 | 15000.50 |
| Ноутбук 12 | 35000.75 |

### Пример 3: Выбрать несколько столбцов в определенном порядке

```sql
SELECT article, name, price, category 
FROM products;
```

**Результат:**
| article | name | price | category |
|---------|------|-------|----------|
| ART-12345-1 | Смартфон 25 | 15000.50 | Электроника |
| ART-67890-2 | Ноутбук 12 | 35000.75 | Компьютеры |

---

## Фильтрация данных (WHERE)

### Операторы сравнения

#### Равенство (=)

```sql
SELECT * FROM products WHERE category = 'Электроника';
```

**Что происходит:**
- Выбираются только товары категории "Электроника"

#### Неравенство (!= или <>)

```sql
SELECT * FROM products WHERE price != 1000;
-- или
SELECT * FROM products WHERE price <> 1000;
```

**Что происходит:**
- Выбираются товары, цена которых не равна 1000

#### Больше/Меньше (>, <, >=, <=)

```sql
-- Товары дороже 10000 рублей
SELECT * FROM products WHERE price > 10000;

-- Товары дешевле или равны 5000 рублей
SELECT * FROM products WHERE price <= 5000;

-- Товары в диапазоне цен
SELECT * FROM products WHERE price >= 5000 AND price <= 15000;
```

### Логические операторы

#### AND (И) - оба условия должны быть истинными

```sql
SELECT * FROM products 
WHERE category = 'Электроника' AND price > 20000;
```

**Что происходит:**
- Выбираются товары, которые:
  - Принадлежат категории "Электроника" **И**
  - Имеют цену больше 20000 рублей

#### OR (ИЛИ) - хотя бы одно условие должно быть истинным

```sql
SELECT * FROM products 
WHERE category = 'Электроника' OR category = 'Компьютеры';
```

**Что происходит:**
- Выбираются товары категории "Электроника" **ИЛИ** "Компьютеры"

#### NOT (НЕ) - инверсия условия

```sql
SELECT * FROM products 
WHERE NOT category = 'Электроника';
```

**Что происходит:**
- Выбираются товары, которые **НЕ** принадлежат категории "Электроника"

### LIKE - поиск по шаблону

```sql
-- Товары, в названии которых есть "Смартфон"
SELECT * FROM products WHERE name LIKE '%Смартфон%';

-- Товары, начинающиеся с "Ноутбук"
SELECT * FROM products WHERE name LIKE 'Ноутбук%';

-- Товары, заканчивающиеся на "1"
SELECT * FROM products WHERE name LIKE '%1';
```

**Символы шаблона:**
- `%` - любое количество любых символов (0 или более)
- `_` - один любой символ

**Примеры:**
- `'%Смартфон%'` - содержит "Смартфон" в любом месте
- `'Смартфон%'` - начинается с "Смартфон"
- `'%Смартфон'` - заканчивается на "Смартфон"
- `'Смартфон_'` - начинается с "Смартфон" и имеет еще один символ

### IN - проверка вхождения в список

```sql
SELECT * FROM products 
WHERE category IN ('Электроника', 'Компьютеры', 'Гаджеты');
```

**Что происходит:**
- Выбираются товары, категория которых входит в список

**Эквивалентно:**
```sql
SELECT * FROM products 
WHERE category = 'Электроника' 
   OR category = 'Компьютеры' 
   OR category = 'Гаджеты';
```

### BETWEEN - диапазон значений

```sql
SELECT * FROM products 
WHERE price BETWEEN 5000 AND 15000;
```

**Что происходит:**
- Выбираются товары с ценой от 5000 до 15000 рублей включительно

**Эквивалентно:**
```sql
SELECT * FROM products 
WHERE price >= 5000 AND price <= 15000;
```

### IS NULL / IS NOT NULL - проверка на NULL

```sql
-- Товары без описания
SELECT * FROM products WHERE description IS NULL;

-- Товары с описанием
SELECT * FROM products WHERE description IS NOT NULL;
```

---

## Сортировка (ORDER BY)

### Сортировка по одному столбцу

```sql
-- Сортировка по цене (по возрастанию)
SELECT * FROM products ORDER BY price;

-- Сортировка по цене (по убыванию)
SELECT * FROM products ORDER BY price DESC;

-- Сортировка по названию (по алфавиту)
SELECT * FROM products ORDER BY name;
```

**Направления сортировки:**
- `ASC` - по возрастанию (по умолчанию)
- `DESC` - по убыванию

### Сортировка по нескольким столбцам

```sql
-- Сначала по категории, затем по цене
SELECT * FROM products 
ORDER BY category, price DESC;
```

**Что происходит:**
- Сначала сортировка по категории (A-Z)
- Затем внутри каждой категории - по цене (от большей к меньшей)

### Пример: Топ-10 самых дорогих товаров

```sql
SELECT name, category, price 
FROM products 
ORDER BY price DESC 
LIMIT 10;
```

---

## Ограничение количества записей (LIMIT)

### LIMIT - ограничение количества строк

```sql
-- Первые 10 товаров
SELECT * FROM products LIMIT 10;

-- Пропустить первые 5, взять следующие 10
SELECT * FROM products LIMIT 10 OFFSET 5;
```

**Что происходит:**
- `LIMIT 10` - возвращает только первые 10 записей
- `OFFSET 5` - пропускает первые 5 записей

**Использование:**
- Пагинация (разбиение на страницы)
- Ограничение больших результатов
- Топ-N записей

### Пример: Пагинация

```sql
-- Страница 1 (записи 1-10)
SELECT * FROM products LIMIT 10 OFFSET 0;

-- Страница 2 (записи 11-20)
SELECT * FROM products LIMIT 10 OFFSET 10;

-- Страница 3 (записи 21-30)
SELECT * FROM products LIMIT 10 OFFSET 20;
```

---

## Группировка (GROUP BY)

### Группировка по одному столбцу

```sql
-- Количество товаров в каждой категории
SELECT category, COUNT(*) AS count
FROM products
GROUP BY category;
```

**Результат:**
| category | count |
|----------|-------|
| Электроника | 150 |
| Компьютеры | 200 |
| Аксессуары | 100 |

### Группировка по нескольким столбцам

```sql
-- Статистика по категориям и ценам
SELECT category, 
       CASE 
           WHEN price < 1000 THEN 'Дешевые'
           WHEN price < 10000 THEN 'Средние'
           ELSE 'Дорогие'
       END AS price_category,
       COUNT(*) AS count
FROM products
GROUP BY category, price_category;
```

---

## Агрегатные функции

Агрегатные функции выполняют вычисления над группами строк.

### COUNT - подсчет количества

```sql
-- Общее количество товаров
SELECT COUNT(*) FROM products;

-- Количество товаров в категории "Электроника"
SELECT COUNT(*) FROM products WHERE category = 'Электроника';

-- Количество уникальных категорий
SELECT COUNT(DISTINCT category) FROM products;
```

### SUM - сумма значений

```sql
-- Общая стоимость всех товаров
SELECT SUM(price) AS total_value FROM products;

-- Сумма цен товаров по категориям
SELECT category, SUM(price) AS total_value
FROM products
GROUP BY category;
```

### AVG - среднее значение

```sql
-- Средняя цена всех товаров
SELECT AVG(price) AS avg_price FROM products;

-- Средняя цена по категориям
SELECT category, AVG(price) AS avg_price
FROM products
GROUP BY category;
```

### MIN / MAX - минимальное/максимальное значение

```sql
-- Самая низкая и высокая цена
SELECT MIN(price) AS min_price, MAX(price) AS max_price
FROM products;

-- Минимальная и максимальная цена по категориям
SELECT category, 
       MIN(price) AS min_price, 
       MAX(price) AS max_price
FROM products
GROUP BY category;
```

### Полная статистика по категориям

```sql
SELECT 
    category,
    COUNT(*) AS count,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    AVG(price) AS avg_price,
    SUM(price) AS total_value
FROM products
GROUP BY category
ORDER BY count DESC;
```

---

## Условия для групп (HAVING)

**HAVING** используется для фильтрации результатов после группировки (GROUP BY).

### Разница между WHERE и HAVING:

- **WHERE** - фильтрует строки **до** группировки
- **HAVING** - фильтрует группы **после** группировки

### Пример: Категории с более чем 50 товарами

```sql
SELECT category, COUNT(*) AS count
FROM products
GROUP BY category
HAVING COUNT(*) > 50;
```

**Что происходит:**
1. Группируем товары по категориям
2. Подсчитываем количество в каждой группе
3. Оставляем только группы с количеством > 50

### Пример: Категории со средней ценой больше 10000

```sql
SELECT category, AVG(price) AS avg_price
FROM products
GROUP BY category
HAVING AVG(price) > 10000
ORDER BY avg_price DESC;
```

### Сравнение WHERE и HAVING

```sql
-- WHERE - фильтрует до группировки
SELECT category, COUNT(*) AS count
FROM products
WHERE price > 5000  -- Фильтруем товары дороже 5000
GROUP BY category;

-- HAVING - фильтрует после группировки
SELECT category, COUNT(*) AS count
FROM products
GROUP BY category
HAVING COUNT(*) > 10;  -- Фильтруем категории с более чем 10 товарами
```

---

## Уникальные значения (DISTINCT)

### DISTINCT - удаление дубликатов

```sql
-- Все уникальные категории
SELECT DISTINCT category FROM products;

-- Уникальные комбинации категории и цены
SELECT DISTINCT category, price FROM products;
```

### DISTINCT с агрегатными функциями

```sql
-- Количество уникальных категорий
SELECT COUNT(DISTINCT category) FROM products;
```

---

## Псевдонимы (ALIAS)

Псевдонимы используются для переименования столбцов или таблиц в результате запроса.

### Псевдонимы столбцов (AS)

```sql
-- Переименование столбцов в результате
SELECT 
    name AS product_name,
    price AS product_price,
    category AS product_category
FROM products;
```

**Результат:**
| product_name | product_price | product_category |
|--------------|---------------|------------------|
| Смартфон 25 | 15000.50 | Электроника |

### AS можно опустить

```sql
-- Оба варианта эквивалентны
SELECT name AS product_name FROM products;
SELECT name product_name FROM products;
```

### Псевдонимы в вычислениях

```sql
SELECT 
    name,
    price,
    price * 1.2 AS price_with_tax,
    price * 0.1 AS discount_10_percent
FROM products;
```

---

## Создание связанной таблицы

Перед изучением JOIN необходимо понять, как создавать связанные таблицы. Связи между таблицами реализуются через **внешние ключи (FOREIGN KEY)**.

### Пример: Таблица заказов (orders)

Создадим таблицу заказов, которая будет связана с таблицей товаров:

```sql
-- Создание таблицы заказов
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    customer_name TEXT NOT NULL,
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    status TEXT NOT NULL DEFAULT 'Новый' CHECK(status IN ('Новый', 'Оплачен', 'Отменен'))
);
```

### Пример: Таблица позиций заказа (order_items)

Создадим промежуточную таблицу, которая связывает заказы и товары (связь many-to-many):

```sql
-- Создание таблицы позиций заказа
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price REAL NOT NULL CHECK(price > 0),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);
```

### Объяснение структуры:

**Таблица `orders`:**
- `id` - первичный ключ заказа
- `order_number` - уникальный номер заказа
- `order_date` - дата создания заказа
- `customer_name` - имя клиента
- `total_amount` - общая сумма заказа
- `status` - статус заказа

**Таблица `order_items`:**
- `id` - первичный ключ позиции
- `order_id` - **внешний ключ** на таблицу `orders`
- `product_id` - **внешний ключ** на таблицу `products`
- `quantity` - количество товара в заказе
- `price` - цена товара на момент заказа

### Внешние ключи (FOREIGN KEY):

```sql
FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
```

**Разбор:**
- **`FOREIGN KEY (order_id)`** - столбец `order_id` является внешним ключом
- **`REFERENCES orders(id)`** - ссылается на столбец `id` таблицы `orders`
- **`ON DELETE CASCADE`** - при удалении заказа автоматически удаляются все его позиции

**Другие варианты:**
- **`ON DELETE RESTRICT`** - запрещает удаление, если есть связанные записи
- **`ON DELETE SET NULL`** - устанавливает NULL при удалении (если столбец допускает NULL)

### Заполнение тестовыми данными:

```sql
-- Вставляем заказы
INSERT INTO orders (order_number, customer_name, total_amount, status) VALUES
('ORD-001', 'Иван Иванов', 45000.50, 'Оплачен'),
('ORD-002', 'Мария Петрова', 25000.00, 'Новый'),
('ORD-003', 'Александр Сидоров', 15000.75, 'Оплачен');

-- Вставляем позиции заказов
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 2, 15000.50),  -- Заказ 1, товар 1, количество 2
(1, 2, 1, 15000.00),  -- Заказ 1, товар 2, количество 1
(2, 3, 1, 25000.00),  -- Заказ 2, товар 3, количество 1
(3, 1, 1, 15000.75);  -- Заказ 3, товар 1, количество 1
```

---

## JOIN - Соединение таблиц

**JOIN** используется для объединения данных из двух или более таблиц на основе связи между ними.

### Зачем нужен JOIN?

Когда данные разнесены по разным таблицам, JOIN позволяет:
- Получить информацию из нескольких таблиц одним запросом
- Объединить связанные данные
- Избежать дублирования данных

### Базовый синтаксис JOIN:

```sql
SELECT columns
FROM table1
JOIN table2 ON table1.column = table2.column;
```

---

## Типы JOIN

### 1. INNER JOIN (Внутреннее соединение)

**INNER JOIN** возвращает только те строки, для которых есть совпадения в обеих таблицах.

```sql
-- Получить информацию о товарах в заказах
SELECT 
    o.order_number,
    o.customer_name,
    p.name AS product_name,
    oi.quantity,
    oi.price,
    (oi.quantity * oi.price) AS total
FROM orders o
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id;
```

**Что происходит:**
- Объединяем таблицы `orders` и `order_items` по `order_id`
- Объединяем результат с таблицей `products` по `product_id`
- Возвращаются только заказы, у которых есть товары

**Визуализация:**
```
orders          order_items      products
-------         -----------      --------
id=1    ----→   order_id=1  ----→  id=1
id=2    ----→   product_id=1       id=2
id=3    ----→   order_id=2  ----→  id=3
                product_id=3
```

**Результат:**
| order_number | customer_name | product_name | quantity | price | total |
|--------------|---------------|--------------|----------|-------|-------|
| ORD-001 | Иван Иванов | Смартфон 25 | 2 | 15000.50 | 30001.00 |
| ORD-001 | Иван Иванов | Ноутбук 12 | 1 | 15000.00 | 15000.00 |

### 2. LEFT JOIN (Левое внешнее соединение)

**LEFT JOIN** возвращает все строки из левой таблицы и соответствующие строки из правой. Если совпадения нет, поля правой таблицы будут NULL.

```sql
-- Все заказы и их товары (даже если товара нет)
SELECT 
    o.order_number,
    o.customer_name,
    p.name AS product_name,
    oi.quantity
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.id;
```

**Что происходит:**
- Возвращаются **все** заказы
- Если у заказа нет товаров, `product_name` и `quantity` будут NULL

**Пример результата:**
| order_number | customer_name | product_name | quantity |
|--------------|---------------|--------------|----------|
| ORD-001 | Иван Иванов | Смартфон 25 | 2 |
| ORD-002 | Мария Петрова | Ноутбук 12 | 1 |
| ORD-004 | Петр Сидоров | NULL | NULL |

### 3. RIGHT JOIN (Правое внешнее соединение)

**RIGHT JOIN** возвращает все строки из правой таблицы и соответствующие строки из левой. Если совпадения нет, поля левой таблицы будут NULL.

```sql
-- Все товары и их заказы (даже если товар не заказан)
SELECT 
    p.name AS product_name,
    o.order_number,
    oi.quantity
FROM orders o
RIGHT JOIN order_items oi ON o.id = oi.order_id
RIGHT JOIN products p ON oi.product_id = p.id;
```

**⚠️ Примечание:** SQLite не поддерживает RIGHT JOIN напрямую, но можно использовать LEFT JOIN с переставленными таблицами.

### 4. FULL OUTER JOIN (Полное внешнее соединение)

**FULL OUTER JOIN** возвращает все строки из обеих таблиц. Если совпадения нет, отсутствующие поля заполняются NULL.

```sql
-- Все заказы и все товары
SELECT 
    o.order_number,
    p.name AS product_name
FROM orders o
FULL OUTER JOIN products p ON ...;
```

**⚠️ Примечание:** SQLite не поддерживает FULL OUTER JOIN напрямую. Можно эмулировать через UNION.

### 5. CROSS JOIN (Декартово произведение)

**CROSS JOIN** возвращает все возможные комбинации строк из обеих таблиц.

```sql
-- Все комбинации заказов и товаров
SELECT 
    o.order_number,
    p.name AS product_name
FROM orders o
CROSS JOIN products p;
```

**⚠️ Осторожно!** CROSS JOIN может вернуть очень много строк (количество заказов × количество товаров).

---

## Практические примеры

### Пример 1: Список товаров в заказе

```sql
SELECT 
    o.order_number,
    o.order_date,
    o.customer_name,
    p.name AS product_name,
    p.category,
    oi.quantity,
    oi.price AS item_price,
    (oi.quantity * oi.price) AS item_total
FROM orders o
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
WHERE o.order_number = 'ORD-001'
ORDER BY oi.id;
```

### Пример 2: Статистика по категориям в заказах

```sql
SELECT 
    p.category,
    COUNT(oi.id) AS orders_count,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.quantity * oi.price) AS total_revenue
FROM products p
INNER JOIN order_items oi ON p.id = oi.product_id
INNER JOIN orders o ON oi.order_id = o.id
GROUP BY p.category
ORDER BY total_revenue DESC;
```

### Пример 3: Товары, которые никогда не заказывались

```sql
SELECT 
    p.id,
    p.name,
    p.category,
    p.price
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
WHERE oi.id IS NULL;
```

**Что происходит:**
- LEFT JOIN возвращает все товары
- Если `oi.id IS NULL`, значит товар не был заказан

### Пример 4: Заказы с общей информацией

```sql
SELECT 
    o.order_number,
    o.customer_name,
    o.order_date,
    COUNT(oi.id) AS items_count,
    SUM(oi.quantity * oi.price) AS calculated_total,
    o.total_amount AS order_total
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.order_number, o.customer_name, o.order_date, o.total_amount;
```

### Пример 5: Самые популярные товары

```sql
SELECT 
    p.name,
    p.category,
    SUM(oi.quantity) AS total_sold,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    SUM(oi.quantity * oi.price) AS total_revenue
FROM products p
INNER JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.category
ORDER BY total_sold DESC
LIMIT 10;
```

### Пример 6: Множественные JOIN

```sql
-- Детальная информация о заказах
SELECT 
    o.order_number,
    o.order_date,
    o.customer_name,
    o.status,
    p.name AS product_name,
    p.category,
    oi.quantity,
    oi.price,
    (oi.quantity * oi.price) AS line_total
FROM orders o
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
WHERE o.status = 'Оплачен'
ORDER BY o.order_date DESC, o.order_number;
```

### Пример 7: Подзапросы с JOIN

```sql
-- Товары, которые заказывались чаще среднего
SELECT 
    p.name,
    p.category,
    COUNT(oi.id) AS order_count
FROM products p
INNER JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.category
HAVING COUNT(oi.id) > (
    SELECT AVG(order_count)
    FROM (
        SELECT COUNT(*) AS order_count
        FROM order_items
        GROUP BY product_id
    )
)
ORDER BY order_count DESC;
```

---

## Псевдонимы таблиц в JOIN

Использование псевдонимов делает запросы короче и читабельнее:

```sql
-- Без псевдонимов (длинно)
SELECT 
    orders.order_number,
    orders.customer_name,
    products.name,
    order_items.quantity
FROM orders
INNER JOIN order_items ON orders.id = order_items.order_id
INNER JOIN products ON order_items.product_id = products.id;

-- С псевдонимами (короче и понятнее)
SELECT 
    o.order_number,
    o.customer_name,
    p.name,
    oi.quantity
FROM orders o
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id;
```

---

## Оптимизация JOIN

### Индексы для ускорения JOIN

```sql
-- Создание индексов для внешних ключей
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
```

Индексы значительно ускоряют выполнение JOIN на больших таблицах.

---

## Заключение

SELECT - это мощный инструмент для работы с данными:

✅ **Базовые операции:** выборка столбцов, фильтрация, сортировка  
✅ **Агрегация:** группировка, подсчет, суммирование  
✅ **Объединение:** JOIN для работы с несколькими таблицами  
✅ **Гибкость:** множество способов комбинирования операций  

Помните:
- Всегда проверяйте условия WHERE перед выполнением
- Используйте индексы для ускорения JOIN
- Выбирайте правильный тип JOIN для вашей задачи
- Тестируйте запросы на небольших данных перед применением к большим таблицам
