"""
Пример использования PostgreSQLDriver в проекте
Демонстрирует работу с базой данных через драйвер
"""
import sys
from postgre_driver import PostgreSQLDriver
from psycopg2 import OperationalError


def create_tables(db: PostgreSQLDriver):
    """
    Создание таблиц для примера (если их еще нет)
    """
    try:
        # Попытка предоставить права на схему public (если возможно)
        try:
            db.execute("GRANT CREATE ON SCHEMA public TO PUBLIC")
            db.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
        except Exception:
            # Если не удалось предоставить права, продолжаем
            pass
        
        # Создание таблицы пользователей с явным указанием схемы
        db.execute("""
            CREATE TABLE IF NOT EXISTS public.users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создание таблицы заказов с явным указанием схемы
        db.execute("""
            CREATE TABLE IF NOT EXISTS public.orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES public.users(id),
                product_name VARCHAR(200) NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✓ Таблицы созданы или уже существуют")
        return True
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Ошибка при создании таблиц: {error_msg}")
        
        # Проверяем, является ли это ошибкой доступа
        if "нет доступа к схеме public" in error_msg.lower() or "permission denied" in error_msg.lower():
            print("\n⚠ Проблема с правами доступа к схеме public.")
            print("Выполните в PostgreSQL следующие команды:")
            print("  GRANT CREATE ON SCHEMA public TO PUBLIC;")
            print("  GRANT ALL ON SCHEMA public TO PUBLIC;")
            print("\nИли выполните от имени суперпользователя:")
            print("  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO PUBLIC;")
        
        return False


def demo_create_operations(db: PostgreSQLDriver):
    """
    Демонстрация операций CREATE
    """
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ: CREATE операции")
    print("="*50)
    
    # Создание 20 пользователей
    print("\n1. Создание пользователей (20 штук)...")
    users_data = [
        {'name': 'Иван Иванов', 'email': 'ivan@example.com', 'age': 30},
        {'name': 'Алексей Петров', 'email': 'alex@example.com', 'age': 25},
        {'name': 'Мария Сидорова', 'email': 'maria@example.com', 'age': 28},
        {'name': 'Петр Смирнов', 'email': 'petr@example.com', 'age': 32},
        {'name': 'Анна Козлова', 'email': 'anna@example.com', 'age': 27},
        {'name': 'Дмитрий Волков', 'email': 'dmitry@example.com', 'age': 35},
        {'name': 'Елена Новикова', 'email': 'elena@example.com', 'age': 29},
        {'name': 'Сергей Морозов', 'email': 'sergey@example.com', 'age': 31},
        {'name': 'Ольга Лебедева', 'email': 'olga@example.com', 'age': 26},
        {'name': 'Андрей Соколов', 'email': 'andrey@example.com', 'age': 33},
        {'name': 'Татьяна Павлова', 'email': 'tatyana@example.com', 'age': 28},
        {'name': 'Николай Орлов', 'email': 'nikolay@example.com', 'age': 36},
        {'name': 'Юлия Федорова', 'email': 'yulia@example.com', 'age': 24},
        {'name': 'Владимир Семенов', 'email': 'vladimir@example.com', 'age': 38},
        {'name': 'Наталья Егорова', 'email': 'natalya@example.com', 'age': 30},
        {'name': 'Игорь Макаров', 'email': 'igor@example.com', 'age': 29},
        {'name': 'Светлана Зайцева', 'email': 'svetlana@example.com', 'age': 27},
        {'name': 'Роман Яковлев', 'email': 'roman@example.com', 'age': 34},
        {'name': 'Екатерина Попова', 'email': 'ekaterina@example.com', 'age': 26},
        {'name': 'Максим Васильев', 'email': 'maxim@example.com', 'age': 32}
    ]
    
    # Проверяем существование пользователей перед вставкой
    existing_emails = []
    for user_data in users_data:
        if db.exists('users', where={'email': user_data['email']}):
            existing_emails.append(user_data['email'])
    
    # Вставляем только новых пользователей
    new_users_data = [u for u in users_data if u['email'] not in existing_emails]
    
    if new_users_data:
        new_ids = db.insert_many('users', new_users_data, returning='id')
        print(f"   ✓ Создано новых пользователей: {len(new_ids)}")
        if existing_emails:
            print(f"   ⚠ Пропущено существующих пользователей: {len(existing_emails)}")
    else:
        new_ids = []
        print(f"   ⚠ Все пользователи уже существуют")
    
    # Получаем всех пользователей (созданных или существующих)
    all_users = db.select('users', order_by='id ASC', as_dict=True)
    user_ids = [user['id'] for user in all_users[:20]]  # Берем первых 20
    
    if not user_ids:
        print("   ✗ Не удалось получить пользователей для создания заказов")
        return None
    
    print(f"   ✓ Всего пользователей в базе: {len(all_users)}")
    print(f"   ✓ Используется для заказов: {len(user_ids)} пользователей")
    
    # Создание более 10 заказов у разных пользователей
    print("\n2. Создание заказов (более 10 штук у разных пользователей)...")
    
    products = [
        ('Ноутбук', 50000.00), ('Мышь', 1500.00), ('Клавиатура', 3000.00),
        ('Монитор', 15000.00), ('Наушники', 5000.00), ('Веб-камера', 3500.00),
        ('Колонки', 4000.00), ('Принтер', 12000.00), ('Сканер', 8000.00),
        ('Планшет', 25000.00), ('Смартфон', 30000.00), ('Умные часы', 15000.00),
        ('Беспроводная мышь', 2000.00), ('Механическая клавиатура', 6000.00),
        ('Игровой монитор', 25000.00), ('Микрофон', 4500.00), ('Графический планшет', 18000.00)
    ]
    
    statuses = ['completed', 'pending', 'processing', 'cancelled']
    
    orders_data = []
    # Создаем заказы для разных пользователей
    for i in range(15):  # Создаем 15 заказов
        user_id = user_ids[i % len(user_ids)]  # Распределяем по пользователям циклически
        product_name, amount = products[i % len(products)]
        status = statuses[i % len(statuses)]
        
        orders_data.append({
            'user_id': user_id,
            'product_name': product_name,
            'amount': amount,
            'status': status
        })
    
    if orders_data:
        order_ids = db.insert_many('orders', orders_data, returning='id')
        print(f"   ✓ Создано заказов: {len(order_ids)}")
        
        # Показываем статистику по пользователям
        print("\n3. Статистика заказов по пользователям:")
        for user in user_ids[:10]:  # Показываем для первых 10
            user_orders = db.count('orders', where={'user_id': user})
            if user_orders > 0:
                user_info = db.select_by_id('users', user, as_dict=True)
                if user_info:
                    print(f"      - {user_info['name']}: {user_orders} заказ(ов)")
    else:
        print(f"   ⚠ Нет данных для создания заказов")
    
    # Возвращаем ID первого пользователя для дальнейших операций
    return user_ids[0] if user_ids else None


def demo_read_operations(db: PostgreSQLDriver, user_id: int):
    """
    Демонстрация операций READ
    """
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ: READ операции")
    print("="*50)
    
    # Выборка всех пользователей
    print("\n1. Выборка всех пользователей...")
    all_users = db.select('users', as_dict=True)
    print(f"   ✓ Найдено пользователей: {len(all_users)}")
    for user in all_users:
        print(f"      - {user['name']} ({user['email']}), возраст: {user['age']}")
    
    # Выборка с условием
    print("\n2. Выборка пользователей старше 27 лет...")
    adults = db.select(
        table='users',
        where={'age': 30},  # Можно использовать более сложные условия через execute
        as_dict=True
    )
    print(f"   ✓ Найдено пользователей с возрастом 30: {len(adults)}")
    
    # Выборка по ID
    print("\n3. Выборка пользователя по ID...")
    user = db.select_by_id('users', user_id, as_dict=True)
    if user:
        print(f"   ✓ Пользователь: {user['name']} ({user['email']})")
    
    # Выборка одной записи
    print("\n4. Поиск пользователя по email...")
    found_user = db.select_one(
        table='users',
        where={'email': 'ivan@example.com'},
        as_dict=True
    )
    if found_user:
        print(f"   ✓ Найден: {found_user['name']}")
    
    # Пагинация
    print("\n5. Пагинация (первые 2 записи)...")
    page = db.select(
        table='users',
        order_by='id ASC',
        limit=2,
        offset=0,
        as_dict=True
    )
    print(f"   ✓ Записей на странице: {len(page)}")
    
    # Подсчет записей
    print("\n6. Подсчет записей...")
    total_users = db.count('users')
    total_orders = db.count('orders')
    print(f"   ✓ Всего пользователей: {total_users}")
    print(f"   ✓ Всего заказов: {total_orders}")
    
    # Проверка существования
    print("\n7. Проверка существования...")
    exists = db.exists('users', where={'email': 'ivan@example.com'})
    print(f"   ✓ Пользователь существует: {exists}")
    
    # Сложный запрос с JOIN
    print("\n8. Сложный запрос (пользователи с заказами)...")
    users_with_orders = db.execute(
        query="""
            SELECT 
                u.id,
                u.name,
                u.email,
                COUNT(o.id) as orders_count,
                COALESCE(SUM(o.amount), 0) as total_amount
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id, u.name, u.email
            ORDER BY orders_count DESC
        """,
        fetch=True,
        as_dict=True
    )
    print(f"   ✓ Найдено записей: {len(users_with_orders)}")
    for record in users_with_orders:
        print(f"      - {record['name']}: {record['orders_count']} заказов, "
              f"на сумму {record['total_amount']} руб.")


def demo_update_operations(db: PostgreSQLDriver, user_id: int):
    """
    Демонстрация операций UPDATE
    """
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ: UPDATE операции")
    print("="*50)
    
    # Обновление по ID
    print("\n1. Обновление пользователя по ID...")
    db.update_by_id(
        table='users',
        id_value=user_id,
        data={'age': 31, 'name': 'Иван Иванович Иванов'}
    )
    updated_user = db.select_by_id('users', user_id, as_dict=True)
    print(f"   ✓ Обновлен пользователь: {updated_user['name']}, возраст: {updated_user['age']}")
    
    # Обновление с условием
    print("\n2. Обновление заказов со статусом 'pending'...")
    updated_count = db.update(
        table='orders',
        data={'status': 'processing'},
        where={'status': 'pending'}
    )
    print(f"   ✓ Обновлено заказов: {len(updated_count) if updated_count else 0}")


def demo_delete_operations(db: PostgreSQLDriver, user_id: int):
    """
    Демонстрация операций DELETE
    """
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ: DELETE операции")
    print("="*50)
    
    # Удаление заказов пользователя
    print("\n1. Удаление заказов пользователя...")
    deleted_orders = db.delete(
        table='orders',
        where={'user_id': user_id}
    )
    print(f"   ✓ Удалено заказов: {len(deleted_orders) if deleted_orders else 0}")
    
    # Удаление пользователя по ID
    print("\n2. Удаление пользователя по ID...")
    deleted_id = db.delete_by_id('users', user_id, returning='id')
    if deleted_id:
        print(f"   ✓ Удален пользователь с ID: {deleted_id}")
    
    # Проверка, что пользователь удален
    remaining = db.count('users')
    print(f"   ✓ Осталось пользователей: {remaining}")


def main():
    """
    Главная функция - демонстрация работы с драйвером
    """
    print("="*50)
    print("ПРИМЕР ИСПОЛЬЗОВАНИЯ PostgreSQLDriver")
    print("="*50)
    
    try:
        # Использование драйвера с контекстным менеджером
        with PostgreSQLDriver() as db:
            # Проверка подключения
            if not db.is_connected():
                print("✗ Не удалось подключиться к базе данных")
                return
            
            print("✓ Подключение к базе данных установлено")
            
            # Создание таблиц
            if not create_tables(db):
                return
            
            # Демонстрация CRUD операций
            user_id = demo_create_operations(db)
            
            if user_id is None:
                print("\n✗ Не удалось создать пользователей для демонстрации")
                return
            
            demo_read_operations(db, user_id)
            demo_update_operations(db, user_id)
            demo_delete_operations(db, user_id)
            
            print("\n" + "="*50)
            print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
            print("="*50)
            print("\nВсе операции выполнены успешно!")
            print("Подключение будет автоматически закрыто.")
            
    except OperationalError as e:
        print(f"\n✗ Ошибка подключения к базе данных: {e}")
        print("\nПроверьте:")
        print("1. Запущен ли сервер PostgreSQL")
        print("2. Правильность параметров подключения в файле .env")
        print("3. Существует ли файл .env с необходимыми переменными")
        return 1
        
    except Exception as e:
        print(f"\n✗ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
 