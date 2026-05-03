"""
Домашнее задание: Агрегирующий запрос PostgreSQL
Сумма заказов по каждому пользователю с LEFT JOIN
"""
import sys
from postgre_driver import PostgreSQLDriver
from psycopg2 import Error, OperationalError


def print_user_totals(db: PostgreSQLDriver):
    """
    Вывод суммы заказов по каждому пользователю в читабельном виде
    """
    try:
        # Получаем данные с помощью метода драйвера
        results = db.get_user_totals(as_dict=True)
        
        print("\n" + "="*60)
        print("СУММА ЗАКАЗОВ ПО КАЖДОМУ ПОЛЬЗОВАТЕЛЮ")
        print("="*60)
        print(f"{'Имя пользователя':<30} {'Email':<25} {'Сумма заказов':>15}")
        print("-"*60)
        
        for record in results:
            name = record['name']
            email = record['email']
            total = float(record['total_amount'])
            
            # Форматируем вывод: Имя — сумма
            print(f"{name:<30} {email:<25} {total:>15.2f} руб.")
        
        print("="*60)
        print(f"Всего пользователей: {len(results)}")
        
        # Подсчитываем пользователей с заказами и без
        users_with_orders = sum(1 for r in results if float(r['total_amount']) > 0)
        users_without_orders = len(results) - users_with_orders
        
        print(f"Пользователей с заказами: {users_with_orders}")
        print(f"Пользователей без заказов: {users_without_orders}")
        
    except Error as e:
        print(f"✗ Ошибка базы данных при получении данных: {e}")
        raise
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")
        raise


def create_sample_data(db: PostgreSQLDriver):
    """
    Создание тестовых данных: минимум 2 заказа на разных пользователей
    """
    try:
        # Проверяем существование пользователей
        users = db.select('users', limit=2, as_dict=True)
        
        if len(users) < 2:
            print("⚠ Недостаточно пользователей для создания заказов")
            return False
        
        user1_id = users[0]['id']
        user2_id = users[1]['id']
        
        # Создаем заказы для разных пользователей
        orders_data = [
            {'user_id': user1_id, 'product_name': 'Ноутбук', 'amount': 50000.00, 'status': 'completed'},
            {'user_id': user1_id, 'product_name': 'Мышь', 'amount': 1500.00, 'status': 'completed'},
            {'user_id': user2_id, 'product_name': 'Клавиатура', 'amount': 3000.00, 'status': 'completed'},
            {'user_id': user2_id, 'product_name': 'Монитор', 'amount': 15000.00, 'status': 'pending'},
        ]
        
        # Проверяем существование заказов перед созданием
        existing_orders = db.count('orders')
        
        if existing_orders < 2:
            db.insert_many('orders', orders_data)
            print(f"✓ Создано заказов: {len(orders_data)}")
        else:
            print(f"✓ Заказы уже существуют (всего: {existing_orders})")
        
        return True
        
    except Error as e:
        print(f"✗ Ошибка базы данных при создании данных: {e}")
        return False
    except Exception as e:
        print(f"✗ Неожиданная ошибка при создании данных: {e}")
        return False


def test_cascade_delete(db: PostgreSQLDriver):
    """
    Проверка ON DELETE CASCADE при удалении пользователя с заказами
    """
    try:
        print("\n" + "="*60)
        print("ПРОВЕРКА ON DELETE CASCADE")
        print("="*60)
        
        # Создаем тестового пользователя с заказами
        test_user_id = db.insert(
            table='users',
            data={
                'name': 'Тестовый Пользователь',
                'email': 'test_cascade@example.com',
                'age': 25
            },
            returning='id'
        )
        
        # Создаем заказы для этого пользователя
        test_orders = [
            {'user_id': test_user_id, 'product_name': 'Тестовый товар 1', 'amount': 1000.00, 'status': 'completed'},
            {'user_id': test_user_id, 'product_name': 'Тестовый товар 2', 'amount': 2000.00, 'status': 'completed'},
        ]
        db.insert_many('orders', test_orders)
        
        orders_before = db.count('orders', where={'user_id': test_user_id})
        print(f"✓ Создан пользователь с ID {test_user_id} и {orders_before} заказами")
        
        # Удаляем пользователя
        db.delete_by_id('users', test_user_id)
        print(f"✓ Пользователь удален")
        
        # Проверяем, что заказы тоже удалены (CASCADE)
        orders_after = db.count('orders', where={'user_id': test_user_id})
        
        if orders_after == 0:
            print(f"✓ ON DELETE CASCADE работает корректно: заказы удалены автоматически")
        else:
            print(f"⚠ Внимание: осталось {orders_after} заказов (CASCADE не работает)")
        
        return True
        
    except Error as e:
        print(f"✗ Ошибка базы данных при проверке CASCADE: {e}")
        return False
    except Exception as e:
        print(f"✗ Неожиданная ошибка при проверке CASCADE: {e}")
        return False


def main():
    """
    Главная функция - выполнение домашнего задания
    """
    print("="*60)
    print("ДОМАШНЕЕ ЗАДАНИЕ: Агрегирующий запрос PostgreSQL")
    print("="*60)
    
    db = None
    
    try:
        # Создаем подключение
        db = PostgreSQLDriver()
        db.connect()
        
        print("\n✓ Подключение к базе данных установлено")
        
        # Создаем таблицы (если еще не созданы)
        print("\n1. Создание таблиц...")
        db.execute("""
            CREATE TABLE IF NOT EXISTS public.users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS public.orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
                product_name VARCHAR(200) NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Таблицы созданы или уже существуют")
        
        # Создаем тестовые данные
        print("\n2. Создание тестовых данных...")
        if not create_sample_data(db):
            print("⚠ Продолжаем с существующими данными...")
        
        # Выполняем агрегирующий запрос
        print("\n3. Выполнение агрегирующего запроса...")
        print_user_totals(db)
        
        # Проверяем ON DELETE CASCADE
        print("\n4. Проверка ON DELETE CASCADE...")
        test_cascade_delete(db)
        
        print("\n" + "="*60)
        print("ДОМАШНЕЕ ЗАДАНИЕ ВЫПОЛНЕНО")
        print("="*60)
        
        return 0
        
    except OperationalError as e:
        print(f"\n✗ Ошибка подключения к базе данных: {e}")
        print("\nПроверьте:")
        print("1. Запущен ли сервер PostgreSQL")
        print("2. Правильность параметров подключения в файле .env")
        print("3. Существует ли файл .env с необходимыми переменными")
        return 1
        
    except Error as e:
        print(f"\n✗ Ошибка базы данных: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    except Exception as e:
        print(f"\n✗ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Гарантированное закрытие соединения
        if db:
            try:
                db.disconnect()
                print("\n✓ Соединение с базой данных закрыто")
            except Exception as e:
                print(f"\n⚠ Ошибка при закрытии соединения: {e}")


if __name__ == "__main__":
    sys.exit(main())
