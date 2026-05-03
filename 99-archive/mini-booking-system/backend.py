"""
Backend модуль для мини-системы бронирования
"""
from postgre_driver import PostgreSQLDriver
from models import user, tables, booking
from models.user import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    get_all_users,
    update_user,
    delete_user
)
from models.tables import (
    create_table,
    get_table_by_id,
    get_table_by_number,
    get_all_tables,
    update_table,
    delete_table
)
from models.booking import (
    create_booking,
    get_booking_by_id,
    get_bookings_by_user,
    get_bookings_by_table,
    get_all_bookings,
    update_booking,
    delete_booking
)
from datetime import datetime, date
from typing import Optional, Dict, Any, List


def create_tables(db: PostgreSQLDriver) -> None:
    """
    Создание всех таблиц в базе данных, если они не существуют
    
    Args:
        db: Экземпляр PostgreSQLDriver
    
    Example:
        from postgre_driver import PostgreSQLDriver
        
        db = PostgreSQLDriver()
        db.connect()
        create_tables(db)
    """
    # Схема таблицы users
    users_schema = {
        'id': 'SERIAL PRIMARY KEY',
        'name': {'type': str, 'constraints': 'NOT NULL', 'size': 255},
        'email': {'type': str, 'constraints': 'UNIQUE NOT NULL', 'size': 255},
        'phone': {'type': str, 'size': 20},
        'password_hash': {'type': str, 'size': 255},
        'role': {'type': str, 'default': 'client', 'size': 20},
        'is_active': {'type': bool, 'default': True},
        'created_at': {'type': datetime, 'default': 'CURRENT_TIMESTAMP'},
        'updated_at': {'type': datetime, 'default': 'CURRENT_TIMESTAMP'}
    }
    
    # Схема таблицы restaurant_tables
    tables_schema = {
        'id': 'SERIAL PRIMARY KEY',
        'table_number': {'type': str, 'constraints': 'UNIQUE NOT NULL', 'size': 50},
        'capacity': {'type': int, 'constraints': 'NOT NULL'},
        'description': {'type': str, 'size': 500},
        'location': {'type': str, 'size': 100},
        'is_available': {'type': bool, 'default': True},
        'created_at': {'type': datetime, 'default': 'CURRENT_TIMESTAMP'},
        'updated_at': {'type': datetime, 'default': 'CURRENT_TIMESTAMP'}
    }
    
    # Схема таблицы bookings
    bookings_schema = {
        'id': 'SERIAL PRIMARY KEY',
        'user_id': {'type': int, 'constraints': 'NOT NULL'},
        'table_id': {'type': int, 'constraints': 'NOT NULL'},
        'booking_date': {'type': 'DATE', 'constraints': 'NOT NULL'},
        'booking_time': {'type': 'TIME', 'constraints': 'NOT NULL'},
        'duration_minutes': {'type': int, 'constraints': 'NOT NULL', 'default': 120},
        'guests_count': {'type': int, 'constraints': 'NOT NULL', 'default': 2},
        'status': {'type': str, 'default': 'pending', 'size': 20},
        'notes': {'type': str, 'size': 1000},
        'created_at': {'type': datetime, 'default': 'CURRENT_TIMESTAMP'},
        'updated_at': {'type': datetime, 'default': 'CURRENT_TIMESTAMP'}
    }
    
    # Создание таблиц
    print("Создание таблиц в базе данных...")
    
    try:
        # Создание таблицы users
        print(f"  → Создание таблицы '{user.TABLE_NAME}'...")
        db.create_table_from_model(user, users_schema)
        print(f"    ✓ Таблица '{user.TABLE_NAME}' готова")
        
        # Создание таблицы restaurant_tables
        print(f"  → Создание таблицы '{tables.TABLE_NAME}'...")
        db.create_table_from_model(tables, tables_schema)
        print(f"    ✓ Таблица '{tables.TABLE_NAME}' готова")
        
        # Создание таблицы bookings
        print(f"  → Создание таблицы '{booking.TABLE_NAME}'...")
        db.create_table_from_model(booking, bookings_schema)
        print(f"    ✓ Таблица '{booking.TABLE_NAME}' готова")
        
        # Создание внешних ключей
        print("  → Создание внешних ключей...")
        _create_foreign_keys(db)
        print("    ✓ Внешние ключи созданы")
        
        print("✓ Все таблицы успешно созданы!")
        
    except Exception as e:
        print(f"✗ Ошибка при создании таблиц: {e}")
        raise


def _create_foreign_keys(db: PostgreSQLDriver) -> None:
    """
    Создание внешних ключей для таблиц
    
    Args:
        db: Экземпляр PostgreSQLDriver
    """
    try:
        # Проверяем существование внешних ключей перед созданием
        with db.get_cursor() as cursor:
            # Внешний ключ bookings.user_id -> users.id
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'fk_bookings_user_id'
                    ) THEN
                        ALTER TABLE bookings 
                        ADD CONSTRAINT fk_bookings_user_id 
                        FOREIGN KEY (user_id) REFERENCES users(id) 
                        ON DELETE CASCADE;
                    END IF;
                END $$;
            """)
            
            # Внешний ключ bookings.table_id -> restaurant_tables.id
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'fk_bookings_table_id'
                    ) THEN
                        ALTER TABLE bookings 
                        ADD CONSTRAINT fk_bookings_table_id 
                        FOREIGN KEY (table_id) REFERENCES restaurant_tables(id) 
                        ON DELETE CASCADE;
                    END IF;
                END $$;
            """)
            
    except Exception as e:
        # Игнорируем ошибки, если ключи уже существуют
        pass


# ==================== CRUD операции ====================
# Все функции экспортируются из моделей для удобного использования

# Users CRUD
__all__ = [
    'create_user',
    'get_all_users',
    'get_user_by_id',
    'update_user',
    'delete_user',
    'create_table',
    'get_all_tables',
    'get_table_by_id',
    'update_table',
    'delete_table',
    'create_booking',
    'get_all_bookings',
    'get_booking_by_id',
    'update_booking',
    'delete_booking',
]


def main():
    """
    Главная функция для запуска скрипта инициализации базы данных
    """
    print("=" * 60)
    print("Инициализация базы данных для мини-системы бронирования")
    print("=" * 60)
    
    # Создаем экземпляр драйвера
    db = PostgreSQLDriver()
    
    try:
        # Подключаемся к базе данных
        print("\nПодключение к базе данных...")
        db.connect()
        print("✓ Подключение установлено")
        
        # Создаем таблицы
        print("\n")
        create_tables(db)
        
        print("\n" + "=" * 60)
        print("Инициализация завершена успешно!")
        print("=" * 60)
        
    except ConnectionError as e:
        print(f"\n✗ Ошибка подключения к базе данных: {e}")
        print("\nПроверьте настройки подключения в файле .env:")
        print("  - DB_HOST")
        print("  - DB_PORT")
        print("  - DB_NAME")
        print("  - DB_USER")
        print("  - DB_PASSWORD")
        return 1
        
    except Exception as e:
        print(f"\n✗ Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Закрываем подключение
        db.disconnect()
        print("\nПодключение закрыто")
    
    return 0


if __name__ == "__main__":
    exit(main())
