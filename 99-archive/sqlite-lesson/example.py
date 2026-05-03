"""
Пример использования модуля database для работы с SQLite3.

Демонстрирует основные операции: создание БД, подключение,
создание таблиц, вставка, чтение, обновление и удаление данных.
"""

import logging
from database import Database

# Настройка логирования для просмотра работы модуля
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def main():
    """Основная функция с примерами использования модуля Database."""
    
    # Указываем путь к базе данных
    db_path = "base.db"
    
    print("=" * 60)
    print("ПРИМЕР ИСПОЛЬЗОВАНИЯ МОДУЛЯ DATABASE")
    print("=" * 60)
    
    # Пример 1: Использование контекстного менеджера (рекомендуемый способ)
    print("\n1. Создание базы данных и подключение через контекстный менеджер")
    print("-" * 60)
    
    with Database(db_path) as db:
        # Создание таблицы пользователей
        print("\n2. Создание таблицы 'users'")
        db.create_table("users", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "age": "INTEGER",
            "email": "TEXT UNIQUE",
            "city": "TEXT"
        })
        
        # Проверка существования таблицы
        if db.table_exists("users"):
            print("✓ Таблица 'users' успешно создана")
        
        # Получение информации о таблице
        print("\n3. Информация о структуре таблицы:")
        table_info = db.get_table_info("users")
        for column in table_info:
            print(f"  - {column['name']}: {column['type']}")
    
    # Пример 2: Вставка данных
    print("\n4. Вставка данных в таблицу")
    print("-" * 60)
    
    with Database(db_path) as db:
        # Вставка одной записи
        user_id_1 = db.insert("users", {
            "name": "Иван Петров",
            "age": 25,
            "email": "ivan@example.com",
            "city": "Москва"
        })
        print(f"✓ Добавлен пользователь с ID: {user_id_1}")
        
        # Вставка еще нескольких записей
        user_id_2 = db.insert("users", {
            "name": "Мария Сидорова",
            "age": 30,
            "email": "maria@example.com",
            "city": "Санкт-Петербург"
        })
        print(f"✓ Добавлен пользователь с ID: {user_id_2}")
        
        user_id_3 = db.insert("users", {
            "name": "Петр Иванов",
            "age": 28,
            "email": "petr@example.com",
            "city": "Казань"
        })
        print(f"✓ Добавлен пользователь с ID: {user_id_3}")
        
        # Массовая вставка данных
        new_users = [
            {"name": "Анна Козлова", "age": 22, "email": "anna@example.com", "city": "Новосибирск"},
            {"name": "Дмитрий Смирнов", "age": 35, "email": "dmitry@example.com", "city": "Екатеринбург"},
            {"name": "Елена Волкова", "age": 27, "email": "elena@example.com", "city": "Краснодар"}
        ]
        db.insert_many("users", new_users)
        print(f"✓ Массово добавлено {len(new_users)} пользователей")
    
    # Пример 3: Чтение данных
    print("\n5. Чтение данных из таблицы")
    print("-" * 60)
    
    with Database(db_path) as db:
        # Получение всех записей
        all_users = db.select("users")
        print(f"\nВсего пользователей в базе: {len(all_users)}")
        for user in all_users:
            print(f"  ID: {user['id']}, Имя: {user['name']}, Возраст: {user['age']}, Город: {user['city']}")
        
        # Получение одной записи
        print("\n6. Поиск конкретного пользователя:")
        user = db.select_one("users", where="name = ?", parameters=("Иван Петров",))
        if user:
            print(f"  Найден: {user['name']}, Email: {user['email']}, Возраст: {user['age']}")
        
        # Выборка с условиями
        print("\n7. Пользователи старше 25 лет:")
        older_users = db.select(
            "users",
            columns=["name", "age", "city"],
            where="age > ?",
            parameters=(25,),
            order_by="age DESC"
        )
        for user in older_users:
            print(f"  {user['name']}, {user['age']} лет, {user['city']}")
        
        # Подсчет записей
        count = db.count("users", where="age > ?", parameters=(25,))
        print(f"\nВсего пользователей старше 25 лет: {count}")
    
    # Пример 4: Обновление данных
    print("\n8. Обновление данных")
    print("-" * 60)
    
    with Database(db_path) as db:
        # Обновление одной записи
        updated_rows = db.update(
            "users",
            {"age": 26, "city": "Москва (обновлено)"},
            "name = ?",
            ("Иван Петров",)
        )
        print(f"✓ Обновлено записей: {updated_rows}")
        
        # Проверка обновления
        updated_user = db.select_one("users", where="name = ?", parameters=("Иван Петров",))
        if updated_user:
            print(f"  Обновленные данные: {updated_user['name']}, Возраст: {updated_user['age']}, Город: {updated_user['city']}")
    
    # Пример 5: Использование транзакций
    print("\n9. Работа с транзакциями")
    print("-" * 60)
    
    with Database(db_path) as db:
        with db.transaction():
            # Несколько операций в одной транзакции
            db.insert("users", {
                "name": "Транзакционный Пользователь",
                "age": 20,
                "email": "transaction@example.com",
                "city": "Тест"
            })
            db.update("users", {"age": 21}, "name = ?", ("Транзакционный Пользователь",))
            print("✓ Транзакция выполнена успешно")
    
    # Пример 6: Удаление данных
    print("\n10. Удаление данных")
    print("-" * 60)
    
    with Database(db_path) as db:
        # Удаление по условию
        deleted_count = db.delete("users", "name = ?", ("Транзакционный Пользователь",))
        print(f"✓ Удалено записей: {deleted_count}")
        
        # Проверка удаления
        remaining_count = db.count("users")
        print(f"Осталось пользователей в базе: {remaining_count}")
    
    # Пример 7: Получение списка всех таблиц
    print("\n11. Список всех таблиц в базе данных")
    print("-" * 60)
    
    with Database(db_path) as db:
        tables = db.get_all_tables()
        print(f"Таблицы в базе данных: {', '.join(tables)}")
    
    # Пример 8: Добавление нового столбца
    print("\n12. Добавление нового столбца в таблицу")
    print("-" * 60)
    
    with Database(db_path) as db:
        db.add_column("users", "phone", "TEXT", "NULL")
        print("✓ Добавлен столбец 'phone' в таблицу 'users'")
        
        # Обновление данных с новым столбцом
        db.update("users", {"phone": "+7 (999) 123-45-67"}, "name = ?", ("Иван Петров",))
        print("✓ Обновлен номер телефона для пользователя")
        
        # Проверка нового столбца
        user_with_phone = db.select_one("users", where="name = ?", parameters=("Иван Петров",))
        if user_with_phone:
            print(f"  Телефон пользователя {user_with_phone['name']}: {user_with_phone.get('phone', 'не указан')}")
    
    # Пример 9: Выполнение произвольного SQL запроса
    print("\n13. Выполнение произвольного SQL запроса")
    print("-" * 60)
    
    with Database(db_path) as db:
        # Использование метода execute для сложных запросов
        result = db.fetchall(
            "SELECT city, COUNT(*) as count   FROM users GROUP BY city ORDER BY count DESC"
        )
        print("Статистика по городам:")
        for row in result:
            print(f"  {row['city']}: {row['count']} пользователей")
    
    # Пример 10: Оптимизация базы данных
    print("\n14. Оптимизация базы данных")
    print("-" * 60)
    
    with Database(db_path) as db:
        db.vacuum()
        print("✓ База данных оптимизирована")
    
    # Пример 11: Создание резервной копии
    print("\n15. Создание резервной копии")
    print("-" * 60)
    
    with Database(db_path) as db:
        backup_path = "example_backup.db"
        db.backup(backup_path)
        print(f"✓ Резервная копия создана: {backup_path}")
    
    # Финальная статистика
    print("\n" + "=" * 60)
    print("ФИНАЛЬНАЯ СТАТИСТИКА")
    print("=" * 60)
    
    with Database(db_path) as db:
        total_users = db.count("users")
        avg_age = db.fetchone("SELECT AVG(age) as avg_age FROM users")
        
        print(f"Всего пользователей: {total_users}")
        if avg_age:
            print(f"Средний возраст: {avg_age['avg_age']:.1f} лет")
        
        print("\nВсе пользователи:")
        all_final = db.select("users", order_by="id ASC")
        for i, user in enumerate(all_final, 1):
            print(f"{i}. {user['name']} ({user['age']} лет) - {user['city']} - {user.get('email', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("ПРИМЕР ЗАВЕРШЕН")
    print("=" * 60)
    print(f"\nБаза данных создана: {db_path}")
    print(f"Резервная копия: example_backup.db")


if __name__ == "__main__":
    main()
