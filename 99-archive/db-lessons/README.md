# Базы данных - Практические задания

Этот проект содержит несколько баз данных для изучения SQL и работы с базами данных.

---

## 📚 Homework - База данных студентов

### Описание
Простая база данных для хранения информации о студентах.

### Структура базы данных

**Таблица `students`:**
- `id` (INTEGER PRIMARY KEY) - уникальный идентификатор
- `first_name` (TEXT) - имя студента
- `last_name` (TEXT) - фамилия студента
- `age` (REAL) - возраст студента
- `is_active` (BOOLEAN) - активен ли студент (1 - да, 0 - нет)

### Файлы

- **`create_homework_db.py`** - Python скрипт для создания базы данных
- **`homework.db`** - файл базы данных SQLite (создается автоматически)

### Как использовать

#### Вариант 1: Python скрипт
```bash
python create_homework_db.py
```

Скрипт автоматически:
- Создаст базу данных `homework.db`
- Создаст таблицу `students`
- Заполнит её 5 тестовыми записями
- Покажет созданные данные

#### Вариант 2: DBeaver
1. Создайте новое подключение к SQLite
2. Укажите путь к файлу `homework.db`
3. Выполните SQL команды вручную:

```sql
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    age REAL,
    is_active BOOLEAN
);

INSERT INTO students (first_name, last_name, age, is_active) VALUES
('Иван', 'Иванов', 20.5, 1),
('Мария', 'Петрова', 19.0, 1),
('Александр', 'Сидоров', 21.0, 0),
('Елена', 'Козлова', 20.0, 1),
('Дмитрий', 'Смирнов', 22.5, 1);
```

### Примеры запросов

```sql
-- Показать всех студентов
SELECT * FROM students;

-- Показать только активных студентов
SELECT * FROM students WHERE is_active = 1;

-- Показать студентов старше 20 лет
SELECT first_name, last_name, age 
FROM students 
WHERE age > 20;

-- Подсчитать количество активных студентов
SELECT COUNT(*) FROM students WHERE is_active = 1;
```

---

## 🍳 Recipes - База данных рецептов (Many-to-Many)

### Описание
База данных для хранения рецептов и продуктов с отношением **many-to-many** (многие-ко-многим). Один рецепт может содержать много продуктов, и один продукт может использоваться во многих рецептах.

### Структура базы данных

**Таблица `products`** (продукты):
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT) - уникальный идентификатор
- `name` (TEXT NOT NULL) - название продукта
- `unit` (TEXT NOT NULL) - единица измерения (г, мл, шт и т.д.)
- `created_at` (DATETIME) - дата создания записи

**Таблица `recipes`** (рецепты):
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT) - уникальный идентификатор
- `name` (TEXT NOT NULL) - название рецепта
- `description` (TEXT) - описание рецепта
- `cooking_time` (INTEGER) - время приготовления в минутах
- `servings` (INTEGER) - количество порций
- `created_at` (DATETIME) - дата создания записи

**Таблица `recipe_products`** (промежуточная таблица для связи many-to-many):
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT) - уникальный идентификатор
- `recipe_id` (INTEGER NOT NULL, FOREIGN KEY) - ссылка на рецепт
- `product_id` (INTEGER NOT NULL, FOREIGN KEY) - ссылка на продукт
- `quantity` (REAL NOT NULL) - количество продукта в рецепте
- `UNIQUE(recipe_id, product_id)` - один продукт может быть в рецепте только один раз

### Файлы

- **`recipes.py`** - Python скрипт для создания базы данных
- **`recipes.sql`** - SQL скрипт для использования в DBeaver
- **`recipes_queries.sql`** - примеры SQL запросов для работы с данными
- **`recipes.db`** - файл базы данных SQLite (создается автоматически)

### Как использовать

#### Вариант 1: Python скрипт (рекомендуется)
```bash
python recipes.py
```

Скрипт автоматически:
- Создаст базу данных `recipes.db`
- Создаст все таблицы с внешними ключами и индексами
- Заполнит базу тестовыми данными (20 продуктов, 7 рецептов, связи)
- Покажет статистику и примеры данных

#### Вариант 2: SQL скрипт в DBeaver
1. Создайте новое подключение к SQLite базе данных `recipes.db`
2. Выполните файл `recipes.sql` - он создаст структуру и заполнит данными
3. Используйте запросы из `recipes_queries.sql` для проверки работы

#### Вариант 3: Командная строка SQLite
```bash
sqlite3 recipes.db < recipes.sql
```

### Особенности реализации

1. **Внешние ключи** - обеспечивают целостность данных
2. **CASCADE DELETE** - при удалении рецепта или продукта автоматически удаляются связанные записи
3. **UNIQUE ограничение** - предотвращает дублирование связей между рецептом и продуктом
4. **Индексы** - ускоряют поиск по `recipe_id` и `product_id`

### Примеры запросов

```sql
-- Показать все продукты в рецепте "Борщ"
SELECT p.name, rp.quantity, p.unit
FROM products p
JOIN recipe_products rp ON p.id = rp.product_id
JOIN recipes r ON rp.recipe_id = r.id
WHERE r.name = 'Борщ';

-- Показать все рецепты, в которых используется "Мука"
SELECT r.name, r.description
FROM recipes r
JOIN recipe_products rp ON r.id = rp.recipe_id
JOIN products p ON rp.product_id = p.id
WHERE p.name = 'Мука';

-- Подсчитать количество продуктов в каждом рецепте
SELECT r.name, COUNT(rp.product_id) AS products_count
FROM recipes r
LEFT JOIN recipe_products rp ON r.id = rp.recipe_id
GROUP BY r.id, r.name
ORDER BY products_count DESC;

-- Показать все продукты и количество рецептов, в которых они используются
SELECT p.name, COUNT(rp.recipe_id) AS recipes_count
FROM products p
LEFT JOIN recipe_products rp ON p.id = rp.product_id
GROUP BY p.id, p.name
ORDER BY recipes_count DESC;
```

### Тестовые данные

База данных содержит:
- **20 продуктов**: Мука, Сахар, Яйца, Молоко, Мясо, Овощи и т.д.
- **7 рецептов**: Борщ, Оладьи, Салат Оливье, Пицца Маргарита, Плов, Блины, Гуляш
- **Связи**: каждый рецепт связан с несколькими продуктами через таблицу `recipe_products`

---

## 📝 Общие примечания

- Все базы данных используют SQLite
- Файлы баз данных создаются в текущей директории
- Python скрипты требуют Python 3.x
- Для работы с базами данных можно использовать DBeaver, DB Browser for SQLite или командную строку SQLite
