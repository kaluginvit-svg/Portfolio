# PostgreSQL Driver - Драйвер для работы с PostgreSQL

Модуль-драйвер для удобной работы с базой данных PostgreSQL. Предоставляет простой и безопасный интерфейс для выполнения CRUD операций.

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` в корне проекта:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
```

## Быстрый старт

```python
from postgre_driver import PostgreSQLDriver

# Использование с контекстным менеджером (рекомендуется)
with PostgreSQLDriver() as db:
    # Вставка записи
    user_id = db.insert(
        table='users',
        data={'name': 'Иван', 'email': 'ivan@example.com'},
        returning='id'
    )
    
    # Выборка записи
    user = db.select_by_id('users', user_id, as_dict=True)
    print(user)
```

## Основные методы

### CREATE - Создание записей

#### `insert(table, data, returning=None)`
Вставка одной записи в таблицу.

**Параметры:**
- `table` (str): Имя таблицы
- `data` (dict): Словарь с данными (ключи - названия колонок)
- `returning` (str, optional): Колонка для возврата значения (например, 'id')

**Пример:**
```python
user_id = db.insert(
    table='users',
    data={
        'name': 'Иван Иванов',
        'email': 'ivan@example.com',
        'age': 30
    },
    returning='id'
)
```

#### `insert_many(table, data_list, returning=None)`
Массовая вставка записей.

**Параметры:**
- `table` (str): Имя таблицы
- `data_list` (list): Список словарей с данными
- `returning` (str, optional): Колонка для возврата значений

**Пример:**
```python
users_data = [
    {'name': 'Алексей', 'email': 'alex@example.com'},
    {'name': 'Мария', 'email': 'maria@example.com'}
]
ids = db.insert_many('users', users_data, returning='id')
```

### READ - Чтение записей

#### `select(table, columns=None, where=None, order_by=None, limit=None, offset=None, as_dict=False)`
Выборка записей из таблицы.

**Параметры:**
- `table` (str): Имя таблицы
- `columns` (list, optional): Список колонок (None = все колонки)
- `where` (dict, optional): Условия WHERE (ключ - колонка, значение - значение)
- `order_by` (str, optional): Колонка для сортировки (можно добавить ASC/DESC)
- `limit` (int, optional): Максимальное количество записей
- `offset` (int, optional): Смещение для пагинации
- `as_dict` (bool): Если True, возвращает словари вместо кортежей

**Пример:**
```python
# Выборка всех записей
users = db.select('users', as_dict=True)

# Выборка с условием
adults = db.select(
    table='users',
    where={'age': 30},
    order_by='name ASC',
    as_dict=True
)

# Пагинация
page1 = db.select('users', limit=10, offset=0, as_dict=True)
```

#### `select_one(table, columns=None, where=None, order_by=None, as_dict=False)`
Выборка одной записи.

**Пример:**
```python
user = db.select_one(
    table='users',
    where={'email': 'ivan@example.com'},
    as_dict=True
)
```

#### `select_by_id(table, id_value, id_column='id', as_dict=False)`
Выборка записи по ID.

**Пример:**
```python
user = db.select_by_id('users', 1, as_dict=True)
```

### UPDATE - Обновление записей

#### `update(table, data, where, returning=None)`
Обновление записей с условием.

**Параметры:**
- `table` (str): Имя таблицы
- `data` (dict): Данные для обновления
- `where` (dict): Условия WHERE (обязательно для безопасности)
- `returning` (str, optional): Колонка для возврата значений

**Пример:**
```python
db.update(
    table='users',
    data={'age': 31},
    where={'email': 'ivan@example.com'}
)
```

#### `update_by_id(table, id_value, data, id_column='id', returning=None)`
Обновление записи по ID.

**Пример:**
```python
db.update_by_id(
    table='users',
    id_value=1,
    data={'age': 31, 'name': 'Иван Петров'}
)
```

### DELETE - Удаление записей

#### `delete(table, where, returning=None)`
Удаление записей с условием.

**Важно:** Условие WHERE обязательно для безопасности (предотвращает случайное удаление всех записей).

**Пример:**
```python
db.delete(
    table='users',
    where={'email': 'ivan@example.com'}
)
```

#### `delete_by_id(table, id_value, id_column='id', returning=None)`
Удаление записи по ID.

**Пример:**
```python
db.delete_by_id('users', 1)
```

### Дополнительные методы

#### `count(table, where=None)`
Подсчет количества записей.

**Пример:**
```python
total = db.count('users')
adults = db.count('users', where={'age': 30})
```

#### `exists(table, where)`
Проверка существования записи.

**Пример:**
```python
if db.exists('users', where={'email': 'ivan@example.com'}):
    print("Пользователь существует")
```

#### `execute(query, params=None, fetch=False, as_dict=False)`
Выполнение произвольного SQL запроса.

**Пример:**
```python
result = db.execute(
    query="SELECT COUNT(*) as total FROM users WHERE age > %s",
    params=(18,),
    fetch=True,
    as_dict=True
)
```

#### `execute_many(query, params_list)`
Выполнение запроса с множественными параметрами.

**Пример:**
```python
db.execute_many(
    query="INSERT INTO users (name, email) VALUES (%s, %s)",
    params_list=[('Иван', 'ivan@example.com'), ('Мария', 'maria@example.com')]
)
```

## Способы использования

### 1. Контекстный менеджер (рекомендуется)

```python
with PostgreSQLDriver() as db:
    users = db.select('users', as_dict=True)
    # Подключение автоматически закроется
```

### 2. Ручное управление подключением

```python
db = PostgreSQLDriver()
db.connect()

try:
    users = db.select('users', as_dict=True)
finally:
    db.disconnect()
```

### 3. Кастомные параметры подключения

```python
db = PostgreSQLDriver(
    host='localhost',
    port=5432,
    database='mydb',
    user='myuser',
    password='mypassword'
)
```

## Работа с транзакциями

Все операции выполняются в транзакциях. При ошибке автоматически выполняется rollback, при успехе - commit.

```python
with PostgreSQLDriver() as db:
    try:
        db.insert('users', {'name': 'Иван'})
        db.insert('orders', {'user_id': 1, 'total': 1000})
        # Если обе операции успешны, выполнится commit
    except Exception:
        # При ошибке автоматически выполнится rollback
        pass
```

## Безопасность

1. **Параметризованные запросы**: Все запросы используют параметризацию для защиты от SQL-инъекций
2. **Обязательные условия WHERE**: Методы `update()` и `delete()` требуют условия WHERE
3. **Валидация данных**: Проверка входных данных перед выполнением запросов

## Обработка ошибок

```python
from postgre_driver import PostgreSQLDriver
from psycopg2 import OperationalError

try:
    with PostgreSQLDriver() as db:
        db.insert('users', {'name': 'Иван'})
except OperationalError as e:
    print(f"Ошибка подключения: {e}")
except Exception as e:
    print(f"Ошибка выполнения запроса: {e}")
```

## Примеры использования

### Пример 1: CRUD операции для пользователей

```python
from postgre_driver import PostgreSQLDriver

with PostgreSQLDriver() as db:
    # CREATE
    user_id = db.insert(
        table='users',
        data={
            'name': 'Иван Иванов',
            'email': 'ivan@example.com',
            'age': 30
        },
        returning='id'
    )
    
    # READ
    user = db.select_by_id('users', user_id, as_dict=True)
    print(f"Создан пользователь: {user}")
    
    # UPDATE
    db.update_by_id('users', user_id, {'age': 31})
    
    # DELETE
    db.delete_by_id('users', user_id)
```

### Пример 2: Пагинация

```python
def get_users_page(page: int, per_page: int = 10):
    with PostgreSQLDriver() as db:
        offset = (page - 1) * per_page
        users = db.select(
            table='users',
            order_by='id ASC',
            limit=per_page,
            offset=offset,
            as_dict=True
        )
        total = db.count('users')
        return {
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page
        }
```

### Пример 3: Сложные запросы

```python
with PostgreSQLDriver() as db:
    # JOIN запрос
    result = db.execute(
        query="""
            SELECT u.name, u.email, COUNT(o.id) as orders_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id, u.name, u.email
            ORDER BY orders_count DESC
        """,
        fetch=True,
        as_dict=True
    )
```

## Требования

- Python 3.7+
- psycopg2-binary
- python-dotenv

## Лицензия

MIT
