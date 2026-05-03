"""
Модуль для работы с базой данных SQLite3.

Предоставляет класс Database для удобной работы с SQLite базами данных,
включая подключение, выполнение запросов, управление транзакциями и т.д.
"""

import sqlite3
import logging
from typing import Optional, List, Tuple, Dict, Any
from contextlib import contextmanager


class Database:
    """
    Класс для работы с базой данных SQLite3.
    
    Поддерживает подключение к базе данных, выполнение SQL запросов,
    управление транзакциями и работу с контекстными менеджерами.
    """
    
    def __init__(self, db_path: str = "base.db"):
        """
        Инициализация объекта базы данных.
        
        Args:
            db_path: Путь к файлу базы данных SQLite. По умолчанию "base.db"
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def connect(self) -> None:
        """
        Подключение к базе данных.
        
        Создает соединение с базой данных и курсор для выполнения запросов.
        Если база данных не существует, она будет создана автоматически.
        """
        self.logger.debug(f"Попытка подключения к базе данных: {self.db_path}")
        try:
            if self.connection is None:
                self.connection = sqlite3.connect(self.db_path)
                self.connection.row_factory = sqlite3.Row  # Возвращает результаты как словари
                self.cursor = self.connection.cursor()
                self.logger.info(f"Успешное подключение к базе данных: {self.db_path}")
            else:
                self.logger.debug("Соединение уже установлено")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при подключении к базе данных {self.db_path}: {e}")
            raise
    
    def disconnect(self) -> None:
        """
        Отключение от базы данных.
        
        Закрывает курсор и соединение с базой данных.
        Если соединение не было установлено, метод ничего не делает.
        """
        self.logger.debug("Попытка отключения от базы данных")
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
                self.logger.debug("Курсор закрыт")
            
            if self.connection:
                self.connection.close()
                self.connection = None
                self.logger.info(f"Отключение от базы данных {self.db_path} выполнено успешно")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при отключении от базы данных: {e}")
            raise
    
    def __enter__(self):
        """
        Вход в контекстный менеджер.
        
        Returns:
            self: Возвращает сам объект Database
        """
        self.logger.debug("Вход в контекстный менеджер")
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Выход из контекстного менеджера.
        
        Автоматически закрывает соединение при выходе из контекста.
        Если произошла ошибка, транзакция откатывается.
        
        Args:
            exc_type: Тип исключения (если было)
            exc_val: Значение исключения (если было)
            exc_tb: Трассировка исключения (если было)
        """
        self.logger.debug("Выход из контекстного менеджера")
        if exc_type is not None:
            self.logger.warning(f"Обнаружена ошибка при выходе из контекста: {exc_type.__name__}: {exc_val}")
            self.rollback()
        self.disconnect()
    
    def commit(self) -> None:
        """
        Сохранение изменений в базе данных.
        
        Подтверждает текущую транзакцию и сохраняет все изменения.
        """
        self.logger.debug("Попытка подтверждения транзакции (commit)")
        try:
            if self.connection:
                self.connection.commit()
                self.logger.info("Транзакция успешно подтверждена")
            else:
                self.logger.warning("Попытка commit без активного соединения")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при подтверждении транзакции: {e}")
            raise
    
    def rollback(self) -> None:
        """
        Откат изменений в базе данных.
        
        Отменяет текущую транзакцию и возвращает базу данных
        в состояние до начала транзакции.
        """
        self.logger.debug("Попытка отката транзакции (rollback)")
        try:
            if self.connection:
                self.connection.rollback()
                self.logger.info("Транзакция успешно откачена")
            else:
                self.logger.warning("Попытка rollback без активного соединения")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при откате транзакции: {e}")
            raise
    
    @contextmanager
    def transaction(self):
        """
        Контекстный менеджер для работы с транзакциями.
        
        Автоматически начинает транзакцию, при успешном завершении
        делает commit, при ошибке - rollback.
        
        Yields:
            self: Возвращает сам объект Database
            
        Example:
            with db.transaction():
                db.insert("users", {"name": "Иван", "age": 25})
                db.update("users", {"age": 26}, "name = 'Иван'")
        """
        self.logger.debug("Начало транзакции")
        try:
            yield self
            self.commit()
            self.logger.debug("Транзакция завершена успешно")
        except Exception as e:
            self.logger.error(f"Ошибка в транзакции, выполняется rollback: {e}")
            self.rollback()
            raise
    
    def execute(self, query: str, parameters: Optional[Tuple] = None) -> sqlite3.Cursor:
        """
        Выполнение SQL запроса.
        
        Args:
            query: SQL запрос для выполнения
            parameters: Параметры для запроса (кортеж или список)
            
        Returns:
            Курсор с результатами выполнения запроса
            
        Raises:
            sqlite3.Error: Если произошла ошибка при выполнении запроса
        """
        self.logger.debug(f"Выполнение SQL запроса: {query[:100]}..." if len(query) > 100 else f"Выполнение SQL запроса: {query}")
        if parameters:
            self.logger.debug(f"Параметры запроса: {parameters}")
        
        try:
            if self.connection is None:
                self.connect()
            
            if parameters:
                result = self.cursor.execute(query, parameters)
            else:
                result = self.cursor.execute(query)
            
            self.logger.debug(f"Запрос выполнен успешно. Затронуто строк: {self.cursor.rowcount}")
            return result
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при выполнении SQL запроса: {e}. Запрос: {query}")
            raise
    
    def executemany(self, query: str, parameters_list: List[Tuple]) -> sqlite3.Cursor:
        """
        Выполнение SQL запроса с множеством параметров.
        
        Полезно для массовой вставки данных.
        
        Args:
            query: SQL запрос для выполнения
            parameters_list: Список кортежей с параметрами
            
        Returns:
            Курсор с результатами выполнения запроса
            
        Example:
            db.executemany(
                "INSERT INTO users (name, age) VALUES (?, ?)",
                [("Иван", 25), ("Мария", 30), ("Петр", 28)]
            )
        """
        self.logger.debug(f"Выполнение массового SQL запроса. Количество записей: {len(parameters_list)}")
        self.logger.debug(f"Запрос: {query[:100]}..." if len(query) > 100 else f"Запрос: {query}")
        
        try:
            if self.connection is None:
                self.connect()
            
            result = self.cursor.executemany(query, parameters_list)
            self.logger.info(f"Массовый запрос выполнен успешно. Затронуто строк: {self.cursor.rowcount}")
            return result
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при выполнении массового SQL запроса: {e}. Запрос: {query}")
            raise
    
    def executescript(self, script: str) -> None:
        """
        Выполнение SQL скрипта с несколькими запросами.
        
        Args:
            script: SQL скрипт для выполнения (может содержать несколько запросов)
        """
        self.logger.debug(f"Выполнение SQL скрипта. Длина скрипта: {len(script)} символов")
        self.logger.debug(f"Скрипт: {script[:200]}..." if len(script) > 200 else f"Скрипт: {script}")
        
        try:
            if self.connection is None:
                self.connect()
            
            self.cursor.executescript(script)
            self.logger.info("SQL скрипт выполнен успешно")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при выполнении SQL скрипта: {e}")
            raise
    
    def fetchone(self, query: str, parameters: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """
        Получение одной записи из базы данных.
        
        Args:
            query: SQL SELECT запрос
            parameters: Параметры для запроса
            
        Returns:
            Словарь с данными записи или None, если запись не найдена
        """
        self.logger.debug("Получение одной записи из базы данных")
        try:
            self.execute(query, parameters)
            row = self.cursor.fetchone()
            
            if row:
                result = dict(row)
                self.logger.debug(f"Запись найдена: {len(result)} полей")
                return result
            self.logger.debug("Запись не найдена")
            return None
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при получении записи: {e}")
            raise
    
    def fetchall(self, query: str, parameters: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Получение всех записей из базы данных.
        
        Args:
            query: SQL SELECT запрос
            parameters: Параметры для запроса
            
        Returns:
            Список словарей с данными записей
        """
        self.logger.debug("Получение всех записей из базы данных")
        try:
            self.execute(query, parameters)
            rows = self.cursor.fetchall()
            result = [dict(row) for row in rows]
            self.logger.debug(f"Получено записей: {len(result)}")
            return result
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при получении всех записей: {e}")
            raise
    
    def fetchmany(self, query: str, size: int = 1, parameters: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Получение указанного количества записей из базы данных.
        
        Args:
            query: SQL SELECT запрос
            size: Количество записей для получения
            parameters: Параметры для запроса
            
        Returns:
            Список словарей с данными записей
        """
        self.logger.debug(f"Получение {size} записей из базы данных")
        try:
            self.execute(query, parameters)
            rows = self.cursor.fetchmany(size)
            result = [dict(row) for row in rows]
            self.logger.debug(f"Получено записей: {len(result)}")
            return result
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при получении записей: {e}")
            raise
    
    def create_table(self, table_name: str, columns: Dict[str, str], if_not_exists: bool = True) -> None:
        """
        Создание таблицы в базе данных.
        
        Args:
            table_name: Имя таблицы
            columns: Словарь, где ключ - имя столбца, значение - тип данных и ограничения
            if_not_exists: Если True, таблица создается только если её не существует
            
        Example:
            db.create_table("users", {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "name": "TEXT NOT NULL",
                "age": "INTEGER",
                "email": "TEXT UNIQUE"
            })
        """
        self.logger.info(f"Создание таблицы: {table_name} с {len(columns)} столбцами")
        try:
            if_not_exists_clause = "IF NOT EXISTS" if if_not_exists else ""
            columns_def = ", ".join([f"{name} {definition}" for name, definition in columns.items()])
            
            query = f"CREATE TABLE {if_not_exists_clause} {table_name} ({columns_def})"
            self.execute(query)
            self.commit()
            self.logger.info(f"Таблица {table_name} успешно создана")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при создании таблицы {table_name}: {e}")
            raise
    
    def drop_table(self, table_name: str, if_exists: bool = True) -> None:
        """
        Удаление таблицы из базы данных.
        
        Args:
            table_name: Имя таблицы для удаления
            if_exists: Если True, ошибка не возникнет, если таблица не существует
        """
        self.logger.warning(f"Удаление таблицы: {table_name}")
        try:
            if_exists_clause = "IF EXISTS" if if_exists else ""
            query = f"DROP TABLE {if_exists_clause} {table_name}"
            self.execute(query)
            self.commit()
            self.logger.info(f"Таблица {table_name} успешно удалена")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при удалении таблицы {table_name}: {e}")
            raise
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """
        Вставка одной записи в таблицу.
        
        Args:
            table_name: Имя таблицы
            data: Словарь с данными для вставки (ключ - имя столбца, значение - значение)
            
        Returns:
            ID последней вставленной записи (lastrowid)
            
        Example:
            db.insert("users", {"name": "Иван", "age": 25, "email": "ivan@example.com"})
        """
        self.logger.debug(f"Вставка записи в таблицу {table_name}")
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            values = tuple(data.values())
            
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            self.execute(query, values)
            self.commit()
            
            row_id = self.cursor.lastrowid
            self.logger.info(f"Запись успешно вставлена в таблицу {table_name}. ID: {row_id}")
            return row_id
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при вставке записи в таблицу {table_name}: {e}")
            raise
    
    def insert_many(self, table_name: str, data_list: List[Dict[str, Any]]) -> None:
        """
        Массовая вставка записей в таблицу.
        
        Args:
            table_name: Имя таблицы
            data_list: Список словарей с данными для вставки
            
        Example:
            db.insert_many("users", [
                {"name": "Иван", "age": 25},
                {"name": "Мария", "age": 30},
                {"name": "Петр", "age": 28}
            ])
        """
        self.logger.debug(f"Массовая вставка {len(data_list)} записей в таблицу {table_name}")
        try:
            if not data_list:
                self.logger.warning("Список данных для вставки пуст")
                return
            
            columns = ", ".join(data_list[0].keys())
            placeholders = ", ".join(["?" for _ in data_list[0]])
            values_list = [tuple(item.values()) for item in data_list]
            
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            self.executemany(query, values_list)
            self.commit()
            self.logger.info(f"Успешно вставлено {len(data_list)} записей в таблицу {table_name}")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при массовой вставке записей в таблицу {table_name}: {e}")
            raise
    
    def select(self, table_name: str, columns: Optional[List[str]] = None, 
               where: Optional[str] = None, parameters: Optional[Tuple] = None,
               order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Выборка записей из таблицы.
        
        Args:
            table_name: Имя таблицы
            columns: Список столбцов для выборки (если None, выбираются все)
            where: Условие WHERE (без ключевого слова WHERE)
            parameters: Параметры для условия WHERE
            order_by: Условие ORDER BY (без ключевого слова ORDER BY)
            limit: Ограничение количества записей
            
        Returns:
            Список словарей с данными записей
            
        Example:
            db.select("users", columns=["name", "age"], where="age > ?", parameters=(25,), order_by="age DESC", limit=10)
        """
        self.logger.debug(f"Выборка записей из таблицы {table_name}")
        try:
            columns_str = ", ".join(columns) if columns else "*"
            query = f"SELECT {columns_str} FROM {table_name}"
            
            if where:
                query += f" WHERE {where}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.fetchall(query, parameters)
            self.logger.debug(f"Выборка из таблицы {table_name} завершена. Найдено записей: {len(result)}")
            return result
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при выборке из таблицы {table_name}: {e}")
            raise
    
    def select_one(self, table_name: str, columns: Optional[List[str]] = None,
                   where: Optional[str] = None, parameters: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """
        Выборка одной записи из таблицы.
        
        Args:
            table_name: Имя таблицы
            columns: Список столбцов для выборки (если None, выбираются все)
            where: Условие WHERE (без ключевого слова WHERE)
            parameters: Параметры для условия WHERE
            
        Returns:
            Словарь с данными записи или None, если запись не найдена
        """
        self.logger.debug(f"Выборка одной записи из таблицы {table_name}")
        try:
            columns_str = ", ".join(columns) if columns else "*"
            query = f"SELECT {columns_str} FROM {table_name}"
            
            if where:
                query += f" WHERE {where}"
            
            query += " LIMIT 1"
            
            result = self.fetchone(query, parameters)
            if result:
                self.logger.debug(f"Запись найдена в таблице {table_name}")
            else:
                self.logger.debug(f"Запись не найдена в таблице {table_name}")
            return result
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при выборке одной записи из таблицы {table_name}: {e}")
            raise
    
    def update(self, table_name: str, data: Dict[str, Any], 
               where: str, parameters: Optional[Tuple] = None) -> int:
        """
        Обновление записей в таблице.
        
        Args:
            table_name: Имя таблицы
            data: Словарь с данными для обновления (ключ - имя столбца, значение - новое значение)
            where: Условие WHERE (без ключевого слова WHERE)
            parameters: Параметры для условия WHERE (добавляются после значений из data)
            
        Returns:
            Количество обновленных записей
            
        Example:
            db.update("users", {"age": 26}, "name = ?", ("Иван",))
        """
        self.logger.debug(f"Обновление записей в таблице {table_name}")
        try:
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            values = tuple(data.values())
            
            if parameters:
                values = values + parameters
            
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
            self.execute(query, values)
            self.commit()
            
            rowcount = self.cursor.rowcount
            self.logger.info(f"Обновлено записей в таблице {table_name}: {rowcount}")
            return rowcount
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при обновлении записей в таблице {table_name}: {e}")
            raise
    
    def delete(self, table_name: str, where: str, parameters: Optional[Tuple] = None) -> int:
        """
        Удаление записей из таблицы.
        
        Args:
            table_name: Имя таблицы
            where: Условие WHERE (без ключевого слова WHERE)
            parameters: Параметры для условия WHERE
            
        Returns:
            Количество удаленных записей
            
        Example:
            db.delete("users", "age < ?", (18,))
        """
        self.logger.warning(f"Удаление записей из таблицы {table_name}")
        try:
            query = f"DELETE FROM {table_name} WHERE {where}"
            self.execute(query, parameters)
            self.commit()
            
            rowcount = self.cursor.rowcount
            self.logger.info(f"Удалено записей из таблицы {table_name}: {rowcount}")
            return rowcount
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при удалении записей из таблицы {table_name}: {e}")
            raise
    
    def count(self, table_name: str, where: Optional[str] = None, 
              parameters: Optional[Tuple] = None) -> int:
        """
        Подсчет количества записей в таблице.
        
        Args:
            table_name: Имя таблицы
            where: Условие WHERE (без ключевого слова WHERE)
            parameters: Параметры для условия WHERE
            
        Returns:
            Количество записей
            
        Example:
            db.count("users", "age > ?", (25,))
        """
        self.logger.debug(f"Подсчет записей в таблице {table_name}")
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            
            if where:
                query += f" WHERE {where}"
            
            result = self.fetchone(query, parameters)
            count = result["count"] if result else 0
            self.logger.debug(f"Количество записей в таблице {table_name}: {count}")
            return count
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при подсчете записей в таблице {table_name}: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Проверка существования таблицы.
        
        Args:
            table_name: Имя таблицы для проверки
            
        Returns:
            True, если таблица существует, False в противном случае
        """
        self.logger.debug(f"Проверка существования таблицы {table_name}")
        try:
            query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """
            result = self.fetchone(query, (table_name,))
            exists = result is not None
            self.logger.debug(f"Таблица {table_name} {'существует' if exists else 'не существует'}")
            return exists
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при проверке существования таблицы {table_name}: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Получение информации о структуре таблицы.
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            Список словарей с информацией о столбцах таблицы
        """
        self.logger.debug(f"Получение информации о структуре таблицы {table_name}")
        try:
            query = f"PRAGMA table_info({table_name})"
            result = self.fetchall(query)
            self.logger.debug(f"Получена информация о {len(result)} столбцах таблицы {table_name}")
            return result
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при получении информации о таблице {table_name}: {e}")
            raise
    
    def get_all_tables(self) -> List[str]:
        """
        Получение списка всех таблиц в базе данных.
        
        Returns:
            Список имен таблиц
        """
        self.logger.debug("Получение списка всех таблиц в базе данных")
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            results = self.fetchall(query)
            tables = [row["name"] for row in results]
            self.logger.debug(f"Найдено таблиц в базе данных: {len(tables)}")
            return tables
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при получении списка таблиц: {e}")
            raise
    
    def add_column(self, table_name: str, column_name: str, column_type: str, 
                   default_value: Optional[str] = None) -> None:
        """
        Добавление столбца в существующую таблицу.
        
        Args:
            table_name: Имя таблицы
            column_name: Имя нового столбца
            column_type: Тип данных столбца
            default_value: Значение по умолчанию (опционально)
            
        Example:
            db.add_column("users", "phone", "TEXT", "NULL")
        """
        self.logger.info(f"Добавление столбца {column_name} в таблицу {table_name}")
        try:
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            
            if default_value is not None:
                query += f" DEFAULT {default_value}"
            
            self.execute(query)
            self.commit()
            self.logger.info(f"Столбец {column_name} успешно добавлен в таблицу {table_name}")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при добавлении столбца {column_name} в таблицу {table_name}: {e}")
            raise
    
    def rename_table(self, old_name: str, new_name: str) -> None:
        """
        Переименование таблицы.
        
        Args:
            old_name: Текущее имя таблицы
            new_name: Новое имя таблицы
        """
        self.logger.info(f"Переименование таблицы {old_name} в {new_name}")
        try:
            query = f"ALTER TABLE {old_name} RENAME TO {new_name}"
            self.execute(query)
            self.commit()
            self.logger.info(f"Таблица успешно переименована: {old_name} -> {new_name}")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при переименовании таблицы {old_name}: {e}")
            raise
    
    def vacuum(self) -> None:
        """
        Оптимизация базы данных.
        
        Освобождает неиспользуемое пространство и оптимизирует структуру базы данных.
        """
        self.logger.info("Запуск оптимизации базы данных (VACUUM)")
        try:
            self.execute("VACUUM")
            self.commit()
            self.logger.info("Оптимизация базы данных завершена успешно")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при оптимизации базы данных: {e}")
            raise
    
    def backup(self, backup_path: str) -> None:
        """
        Создание резервной копии базы данных.
        
        Args:
            backup_path: Путь для сохранения резервной копии
        """
        self.logger.info(f"Создание резервной копии базы данных в {backup_path}")
        try:
            if self.connection is None:
                self.connect()
            
            backup_conn = sqlite3.connect(backup_path)
            self.connection.backup(backup_conn)
            backup_conn.close()
            self.logger.info(f"Резервная копия успешно создана: {backup_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка при создании резервной копии: {e}")
            raise
