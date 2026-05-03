# SQL UPDATE - Обновление данных в таблице

## 📋 Содержание
1. [Обзор оператора UPDATE](#обзор-оператора-update)
2. [Базовый синтаксис](#базовый-синтаксис)
3. [Обновление одной записи](#обновление-одной-записи)
4. [Обновление нескольких записей](#обновление-нескольких-записей)
5. [Обновление всех записей](#обновление-всех-записей)
6. [Обновление нескольких столбцов](#обновление-нескольких-столбцов)
7. [Использование WHERE с условиями](#использование-where-с-условиями)
8. [Обновление с использованием подзапросов](#обновление-с-использованием-подзапросов)
9. [Безопасность и лучшие практики](#безопасность-и-лучшие-практики)
10. [Примеры для таблицы Products](#примеры-для-таблицы-products)

---

## Обзор оператора UPDATE

**UPDATE** - это SQL-команда для изменения (обновления) существующих записей в таблице базы данных.

### Когда используется UPDATE?

- Изменение цены товара
- Обновление описания продукта
- Изменение категории товара
- Корректировка артикула
- Массовое обновление данных по условию

### ⚠️ Важно!

**UPDATE изменяет данные навсегда!** Всегда проверяйте условие WHERE перед выполнением команды. Рекомендуется сначала выполнить SELECT с теми же условиями, чтобы увидеть, какие записи будут изменены.

---

## Базовый синтаксис

```sql
UPDATE table_name
SET column1 = value1, column2 = value2, ...
WHERE condition;
```

### Разбор синтаксиса:

- **`UPDATE table_name`** - указывает таблицу, в которой нужно обновить данные
- **`SET`** - ключевое слово, после которого перечисляются столбцы и их новые значения
- **`column = value`** - присваивание нового значения столбцу
- **`WHERE condition`** - условие, определяющее, какие строки нужно обновить
  - ⚠️ **БЕЗ WHERE обновятся ВСЕ записи в таблице!**

---

## Обновление одной записи

### Пример 1: Обновление цены конкретного товара по ID

```sql
UPDATE products
SET price = 15000.00
WHERE id = 1;
```

**Что происходит:**
- Находится товар с `id = 1`
- Его цена изменяется на 15000.00 рублей

**Перед выполнением проверьте:**
```sql
SELECT id, name, price 
FROM products 
WHERE id = 1;
```

### Пример 2: Обновление товара по артикулу

```sql
UPDATE products
SET price = 25000.50
WHERE article = 'ART-12345-1';
```

**Что происходит:**
- Находится товар с артикулом `ART-12345-1`
- Его цена обновляется до 25000.50 рублей

---

## Обновление нескольких записей

### Пример 3: Обновление всех товаров в категории

```sql
UPDATE products
SET price = price * 1.1  -- Увеличиваем цену на 10%
WHERE category = 'Электроника';
```

**Что происходит:**
- Находятся все товары категории "Электроника"
- Цена каждого товара увеличивается на 10%
- `price * 1.1` - используем текущее значение цены для расчета

**Проверка перед выполнением:**
```sql
SELECT id, name, category, price, price * 1.1 AS new_price
FROM products
WHERE category = 'Электроника';
```

### Пример 4: Обновление товаров с ценой меньше определенной суммы

```sql
UPDATE products
SET price = price + 500.00
WHERE price < 1000.00;
```

**Что происходит:**
- Находятся все товары с ценой меньше 1000 рублей
- К цене каждого товара добавляется 500 рублей

---

## Обновление всех записей

### ⚠️ ОСТОРОЖНО! Обновление всех записей

```sql
UPDATE products
SET price = price * 0.9;  -- Снижаем все цены на 10%
```

**Что происходит:**
- **ВСЕ** товары в таблице получают новую цену (старая цена * 0.9)
- Это может быть опасно, если вы не хотите изменить все записи!

**Рекомендация:** Всегда используйте WHERE, если не хотите обновить все записи.

---

## Обновление нескольких столбцов

### Пример 5: Обновление цены и описания одновременно

```sql
UPDATE products
SET 
    price = 19999.99,
    description = 'Обновленное описание товара. Высокое качество и надежность.'
WHERE id = 5;
```

**Что происходит:**
- Обновляется товар с `id = 5`
- Изменяются два столбца: `price` и `description`

### Пример 6: Массовое обновление нескольких полей

```sql
UPDATE products
SET 
    category = 'Премиум товары',
    description = description || ' Премиум качество.',
    price = price * 1.2
WHERE price > 30000;
```

**Что происходит:**
- Находятся товары дороже 30000 рублей
- Категория меняется на "Премиум товары"
- К описанию добавляется текст "Премиум качество."
- Цена увеличивается на 20%

**Оператор `||`** - конкатенация (объединение) строк в SQLite.

---

## Использование WHERE с условиями

### Логические операторы

#### AND (И) - оба условия должны быть истинными

```sql
UPDATE products
SET price = price * 0.95
WHERE category = 'Электроника' AND price > 20000;
```

**Что происходит:**
- Обновляются только товары, которые:
  - Принадлежат категории "Электроника" **И**
  - Имеют цену больше 20000 рублей

#### OR (ИЛИ) - хотя бы одно условие должно быть истинным

```sql
UPDATE products
SET category = 'Распродажа'
WHERE price < 1000 OR price > 50000;
```

**Что происходит:**
- Обновляются товары с ценой меньше 1000 **ИЛИ** больше 50000 рублей

#### NOT (НЕ) - инверсия условия

```sql
UPDATE products
SET description = 'Требует обновления описания'
WHERE NOT (description LIKE '%качественный%');
```

**Что происходит:**
- Обновляются товары, в описании которых **НЕТ** слова "качественный"

### Операторы сравнения

| Оператор | Описание | Пример |
|----------|----------|--------|
| `=` | Равно | `WHERE price = 1000` |
| `!=` или `<>` | Не равно | `WHERE price != 1000` |
| `>` | Больше | `WHERE price > 1000` |
| `<` | Меньше | `WHERE price < 1000` |
| `>=` | Больше или равно | `WHERE price >= 1000` |
| `<=` | Меньше или равно | `WHERE price <= 1000` |

### LIKE для поиска по шаблону

```sql
UPDATE products
SET category = 'Смартфоны'
WHERE name LIKE '%Смартфон%';
```

**Что происходит:**
- Находятся товары, в названии которых есть слово "Смартфон"
- `%` - означает любое количество любых символов

**Примеры шаблонов:**
- `'%Смартфон%'` - содержит "Смартфон" в любом месте
- `'Смартфон%'` - начинается с "Смартфон"
- `'%Смартфон'` - заканчивается на "Смартфон"

### IN - проверка вхождения в список

```sql
UPDATE products
SET price = price * 1.15
WHERE category IN ('Электроника', 'Компьютеры', 'Гаджеты');
```

**Что происходит:**
- Обновляются товары, категория которых входит в список: "Электроника", "Компьютеры" или "Гаджеты"

### BETWEEN - диапазон значений

```sql
UPDATE products
SET description = description || ' Популярный товар.'
WHERE price BETWEEN 5000 AND 15000;
```

**Что происходит:**
- Обновляются товары с ценой от 5000 до 15000 рублей включительно
- Эквивалентно: `WHERE price >= 5000 AND price <= 15000`

---

## Обновление с использованием подзапросов

### Пример 7: Обновление на основе среднего значения

```sql
UPDATE products
SET price = price * 0.9
WHERE price > (SELECT AVG(price) FROM products);
```

**Что происходит:**
- Подзапрос `(SELECT AVG(price) FROM products)` вычисляет среднюю цену всех товаров
- Обновляются товары, цена которых выше средней

**Проверка:**
```sql
SELECT AVG(price) AS avg_price FROM products;
SELECT * FROM products WHERE price > (SELECT AVG(price) FROM products);
```

### Пример 8: Обновление на основе данных другой таблицы

Предположим, у нас есть таблица `discounts` с категориями и скидками:

```sql
-- Создаем таблицу скидок (пример)
CREATE TABLE discounts (
    category TEXT PRIMARY KEY,
    discount_percent REAL
);

INSERT INTO discounts VALUES
('Электроника', 10),
('Компьютеры', 15),
('Аксессуары', 5);

-- Обновляем цены на основе скидок
UPDATE products
SET price = price * (1 - (SELECT discount_percent FROM discounts 
                          WHERE discounts.category = products.category) / 100.0)
WHERE EXISTS (
    SELECT 1 FROM discounts 
    WHERE discounts.category = products.category
);
```

**Что происходит:**
- Для каждой категории товаров берется процент скидки из таблицы `discounts`
- Цена обновляется с учетом скидки
- `EXISTS` проверяет, есть ли скидка для данной категории

---

## Безопасность и лучшие практики

### ✅ Рекомендации:

1. **Всегда проверяйте условие WHERE перед UPDATE**
   ```sql
   -- Сначала проверьте, что будет изменено
   SELECT * FROM products WHERE category = 'Электроника';
   
   -- Затем выполняйте UPDATE
   UPDATE products SET price = price * 1.1 WHERE category = 'Электроника';
   ```

2. **Используйте транзакции для отката изменений**
   ```sql
   BEGIN TRANSACTION;
   
   UPDATE products SET price = price * 1.1 WHERE category = 'Электроника';
   
   -- Проверьте результат
   SELECT * FROM products WHERE category = 'Электроника';
   
   -- Если всё правильно - подтвердите
   COMMIT;
   
   -- Если что-то не так - откатите
   -- ROLLBACK;
   ```

3. **Делайте резервные копии перед массовыми обновлениями**
   ```sql
   -- Создайте копию таблицы
   CREATE TABLE products_backup AS SELECT * FROM products;
   ```

4. **Используйте LIMIT для тестирования (если поддерживается)**
   ```sql
   -- В некоторых СУБД можно ограничить количество обновляемых строк
   UPDATE products SET price = price * 1.1 WHERE category = 'Электроника' LIMIT 10;
   ```

5. **Проверяйте количество затронутых строк**
   ```sql
   -- После UPDATE проверьте, сколько строк было изменено
   -- В SQLite это можно сделать через изменения в SELECT
   ```

### ⚠️ Частые ошибки:

1. **Забыли WHERE - обновили все записи!**
   ```sql
   -- ОПАСНО! Обновит все товары
   UPDATE products SET price = 1000;
   
   -- ПРАВИЛЬНО
   UPDATE products SET price = 1000 WHERE id = 1;
   ```

2. **Неправильное условие WHERE**
   ```sql
   -- ОПАСНО! Может обновить не те записи
   UPDATE products SET price = 0 WHERE price = price;  -- Обновит все!
   
   -- ПРАВИЛЬНО
   UPDATE products SET price = 0 WHERE id = 1;
   ```

3. **Использование = вместо LIKE для текста**
   ```sql
   -- Не найдет, если есть пробелы или регистр отличается
   UPDATE products SET category = 'Электроника' WHERE name = 'Смартфон 1';
   
   -- ПРАВИЛЬНО
   UPDATE products SET category = 'Электроника' WHERE name LIKE '%Смартфон%';
   ```

---

## Примеры для таблицы Products

### Структура таблицы products:

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK(price > 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Практические примеры:

#### 1. Обновление цены конкретного товара

```sql
-- Найти товар
SELECT id, name, price FROM products WHERE article = 'ART-12345-1';

-- Обновить цену
UPDATE products
SET price = 15999.99
WHERE article = 'ART-12345-1';

-- Проверить результат
SELECT id, name, price FROM products WHERE article = 'ART-12345-1';
```

#### 2. Массовое повышение цен на 5%

```sql
-- Проверить, сколько товаров будет затронуто
SELECT COUNT(*) AS count, 
       MIN(price) AS min_price, 
       MAX(price) AS max_price,
       AVG(price) AS avg_price
FROM products
WHERE category = 'Электроника';

-- Выполнить обновление
UPDATE products
SET price = price * 1.05
WHERE category = 'Электроника';

-- Проверить результат
SELECT COUNT(*) AS count, 
       MIN(price) AS min_price, 
       MAX(price) AS max_price,
       AVG(price) AS avg_price
FROM products
WHERE category = 'Электроника';
```

#### 3. Обновление описания для дорогих товаров

```sql
UPDATE products
SET description = 'Премиум товар. ' || COALESCE(description, '')
WHERE price > 30000;

-- COALESCE(description, '') - если description NULL, использует пустую строку
```

#### 4. Исправление опечаток в категориях

```sql
-- Найти товары с неправильной категорией
SELECT DISTINCT category FROM products WHERE category LIKE '%электро%';

-- Исправить категорию
UPDATE products
SET category = 'Электроника'
WHERE category IN ('Электроника', 'электроника', 'ЭЛЕКТРОНИКА');
```

#### 5. Обновление артикулов (осторожно с UNIQUE!)

```sql
-- Проверить, не существует ли уже новый артикул
SELECT COUNT(*) FROM products WHERE article = 'ART-NEW-001';

-- Если результат 0, можно обновлять
UPDATE products
SET article = 'ART-NEW-001'
WHERE id = 1;
```

#### 6. Обновление нескольких полей с условиями

```sql
UPDATE products
SET 
    category = 'Распродажа',
    price = price * 0.7,
    description = description || ' Скидка 30%!'
WHERE price > 20000 AND category = 'Электроника';
```

#### 7. Обновление на основе текущей даты

```sql
-- Добавить пометку о последнем обновлении (если есть поле updated_at)
-- Предположим, мы добавили поле updated_at
ALTER TABLE products ADD COLUMN updated_at DATETIME;

UPDATE products
SET 
    price = price * 1.1,
    updated_at = CURRENT_TIMESTAMP
WHERE category = 'Компьютеры';
```

#### 8. Условное обновление с CASE

```sql
UPDATE products
SET price = CASE
    WHEN price < 1000 THEN price * 1.2      -- Дешевые товары +20%
    WHEN price BETWEEN 1000 AND 10000 THEN price * 1.1  -- Средние +10%
    ELSE price * 1.05                       -- Дорогие +5%
END
WHERE category = 'Электроника';
```

---

## Проверка результатов UPDATE

### После выполнения UPDATE всегда проверяйте результат:

```sql
-- 1. Проверьте количество обновленных записей
SELECT COUNT(*) 
FROM products 
WHERE category = 'Электроника' AND price > 20000;

-- 2. Посмотрите примеры обновленных записей
SELECT id, name, category, price 
FROM products 
WHERE category = 'Электроника' 
LIMIT 10;

-- 3. Проверьте статистику
SELECT 
    category,
    COUNT(*) AS count,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    AVG(price) AS avg_price
FROM products
GROUP BY category;
```

---

## Заключение

Оператор UPDATE - мощный инструмент для изменения данных в базе. Помните:

✅ **Всегда используйте WHERE** (кроме случаев, когда действительно нужно обновить все записи)  
✅ **Проверяйте условие через SELECT перед UPDATE**  
✅ **Используйте транзакции для безопасности**  
✅ **Делайте резервные копии перед массовыми обновлениями**  
✅ **Проверяйте результаты после UPDATE**

Следование этим правилам поможет избежать потери данных и ошибок при работе с базой данных.
