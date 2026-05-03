"""
Примеры использования модуля db_driver.py
"""
from postgre_driver import PostgreSQLDriver

# Пример 1: Базовое использование с контекстным менеджером
def example_basic_usage():
    """Базовое использование драйвера"""
    with PostgreSQLDriver() as db:
        # CREATE - Вставка одной записи
        user_id = db.insert(
            table='users',
            data={
                'name': 'Иван Иванов',
                'email': 'ivan@example.com',
                'age': 30
            },
            returning='id'
        )
        print(f"Создан пользователь с ID: {user_id}")
        
        # READ - Выборка всех записей
        users = db.select('users', as_dict=True)
        print(f"Всего пользователей: {len(users)}")
        
        # READ - Выборка с условием
        user = db.select_one(
            table='users',
            where={'email': 'ivan@example.com'},
            as_dict=True
        )
        print(f"Найденный пользователь: {user}")
        
        # UPDATE - Обновление записи
        db.update_by_id(
            table='users',
            id_value=user_id,
            data={'age': 31},
            returning='id'
        )
        print(f"Пользователь обновлен")
        
        # DELETE - Удаление записи
        db.delete_by_id('users', user_id)
        print(f"Пользователь удален")


# Пример 2: Массовая вставка
def example_bulk_insert():
    """Пример массовой вставки данных"""
    with PostgreSQLDriver() as db:
        users_data = [
            {'name': 'Алексей', 'email': 'alex@example.com', 'age': 25},
            {'name': 'Мария', 'email': 'maria@example.com', 'age': 28},
            {'name': 'Петр', 'email': 'petr@example.com', 'age': 32}
        ]
        
        ids = db.insert_many('users', users_data, returning='id')
        print(f"Создано пользователей: {ids}")


# Пример 3: Работа с пагинацией
def example_pagination():
    """Пример работы с пагинацией"""
    with PostgreSQLDriver() as db:
        # Получить первые 10 записей
        page1 = db.select(
            table='users',
            order_by='id ASC',
            limit=10,
            offset=0,
            as_dict=True
        )
        
        # Получить следующие 10 записей
        page2 = db.select(
            table='users',
            order_by='id ASC',
            limit=10,
            offset=10,
            as_dict=True
        )
        
        print(f"Страница 1: {len(page1)} записей")
        print(f"Страница 2: {len(page2)} записей")


# Пример 4: Подсчет и проверка существования
def example_count_and_exists():
    """Пример подсчета и проверки существования"""
    with PostgreSQLDriver() as db:
        # Подсчет всех пользователей
        total = db.count('users')
        print(f"Всего пользователей: {total}")
        
        # Подсчет с условием
        adults = db.count('users', where={'age': 30})
        print(f"Пользователей с возрастом 30: {adults}")
        
        # Проверка существования
        exists = db.exists('users', where={'email': 'ivan@example.com'})
        print(f"Пользователь существует: {exists}")


# Пример 5: Произвольные SQL запросы
def example_custom_queries():
    """Пример выполнения произвольных SQL запросов"""
    with PostgreSQLDriver() as db:
        # Выполнение произвольного запроса
        result = db.execute(
            query="SELECT COUNT(*) as total, AVG(age) as avg_age FROM users",
            fetch=True,
            as_dict=True
        )
        print(f"Статистика: {result}")
        
        # Сложный запрос с JOIN
        result = db.execute(
            query="""
                SELECT u.name, u.email, COUNT(o.id) as orders_count
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                GROUP BY u.id, u.name, u.email
            """,
            fetch=True,
            as_dict=True
        )
        print(f"Пользователи с количеством заказов: {result}")


# Пример 6: Ручное управление подключением
def example_manual_connection():
    """Пример ручного управления подключением"""
    db = PostgreSQLDriver()
    
    try:
        db.connect()
        
        # Выполнение операций
        users = db.select('users', as_dict=True)
        print(f"Найдено пользователей: {len(users)}")
        
    finally:
        db.disconnect()


if __name__ == "__main__":
    print("Примеры использования PostgreSQLDriver")
    print("=" * 50)
    
    # Раскомментируйте нужный пример для запуска
    # example_basic_usage()
    # example_bulk_insert()
    # example_pagination()
    # example_count_and_exists()
    # example_custom_queries()
    # example_manual_connection()
