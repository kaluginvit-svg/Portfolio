"""
Модуль-драйвер для работы с PostgreSQL
Предоставляет класс PostgreSQLDriver с CRUD-методами для работы с базой данных
"""
import os
import psycopg2
from psycopg2 import OperationalError, Error
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime, date, time

# Загрузка переменных окружения из файла .env
load_dotenv()


class PostgreSQLDriver:
    """
    Класс-драйвер для работы с PostgreSQL базой данных
    Предоставляет CRUD-методы и удобные функции для работы с БД
    """
    
    def __init__(self, 
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 database: Optional[str] = None,
                 user: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Инициализация драйвера с параметрами подключения
        
        Args:
            host: Хост базы данных (по умолчанию из DB_HOST)
            port: Порт базы данных (по умолчанию из DB_PORT)
            database: Имя базы данных (по умолчанию из DB_NAME)
            user: Имя пользователя (по умолчанию из DB_USER)
            password: Пароль (по умолчанию из DB_PASSWORD)
        """
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.database = database or os.getenv('DB_NAME', 'postgres')
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', '')
        self._connection: Optional[psycopg2.extensions.connection] = None
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """
        Получение параметров подключения
        
        Returns:
            Словарь с параметрами подключения
        """
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }
    
    def connect(self) -> bool:
        """
        Подключение к базе данных
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        try:
            if self._connection and not self._connection.closed:
                return True
            
            connection_params = self._get_connection_params()
            self._connection = psycopg2.connect(**connection_params)
            self._connection.set_client_encoding('UTF8')
            
            # Установка search_path для работы со схемой public
            with self._connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")
                self._connection.commit()
            
            return True
        except OperationalError as e:
            raise ConnectionError(f"Ошибка подключения к базе данных: {e}")
        except Exception as e:
            raise ConnectionError(f"Неожиданная ошибка при подключении: {e}")
    
    def disconnect(self) -> None:
        """
        Закрытие подключения к базе данных
        """
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None
    
    def is_connected(self) -> bool:
        """
        Проверка состояния подключения
        
        Returns:
            True если подключение активно, False в противном случае
        """
        return self._connection is not None and not self._connection.closed
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = False):
        """
        Контекстный менеджер для работы с курсором
        
        Args:
            dict_cursor: Если True, используется RealDictCursor (возвращает словари)
        
        Yields:
            Курсор для выполнения запросов
        """
        if not self.is_connected():
            self.connect()
        
        cursor_class = RealDictCursor if dict_cursor else psycopg2.extensions.cursor
        cursor = self._connection.cursor(cursor_factory=cursor_class)
        
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    # ==================== CREATE методы ====================
    
    def insert(self, 
               table: str, 
               data: Dict[str, Any],
               returning: Optional[str] = None) -> Optional[Any]:
        """
        Вставка одной записи в таблицу
        
        Args:
            table: Имя таблицы
            data: Словарь с данными для вставки (ключи - названия колонок)
            returning: Колонка для возврата значения (например, 'id')
        
        Returns:
            Значение возвращаемой колонки или None
        """
        if not data:
            raise ValueError("Данные для вставки не могут быть пустыми")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, values)
            if returning:
                result = cursor.fetchone()
                return result[0] if result else None
            return None
    
    def insert_many(self,
                    table: str,
                    data_list: List[Dict[str, Any]],
                    returning: Optional[str] = None) -> List[Any]:
        """
        Массовая вставка записей в таблицу
        
        Args:
            table: Имя таблицы
            data_list: Список словарей с данными для вставки
            returning: Колонка для возврата значений (например, 'id')
        
        Returns:
            Список значений возвращаемой колонки
        """
        if not data_list:
            return []
        
        # Проверяем, что все словари имеют одинаковые ключи
        first_keys = set(data_list[0].keys())
        if not all(set(item.keys()) == first_keys for item in data_list):
            raise ValueError("Все записи должны иметь одинаковые ключи")
        
        columns = ', '.join(data_list[0].keys())
        values = [tuple(item.values()) for item in data_list]
        
        query = f"INSERT INTO {table} ({columns}) VALUES %s"
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            if returning:
                # execute_values с fetch=True возвращает результаты напрямую
                results = execute_values(cursor, query, values, fetch=True)
                return [row[0] for row in results] if results else []
            else:
                execute_values(cursor, query, values)
                return []
    
    # ==================== READ методы ====================
    
    def select(self,
               table: str,
               columns: Optional[List[str]] = None,
               where: Optional[Dict[str, Any]] = None,
               order_by: Optional[str] = None,
               limit: Optional[int] = None,
               offset: Optional[int] = None,
               as_dict: bool = False) -> List[Any]:
        """
        Выборка записей из таблицы
        
        Args:
            table: Имя таблицы
            columns: Список колонок для выборки (None = все колонки)
            where: Словарь условий WHERE (ключ - колонка, значение - значение для сравнения)
            order_by: Колонка для сортировки (можно добавить ASC/DESC)
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            as_dict: Если True, возвращает список словарей вместо кортежей
        
        Returns:
            Список записей (кортежи или словари)
        """
        cols = ', '.join(columns) if columns else '*'
        query = f"SELECT {cols} FROM {table}"
        params = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        if offset:
            query += f" OFFSET {offset}"
        
        with self.get_cursor(dict_cursor=as_dict) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def select_one(self,
                   table: str,
                   columns: Optional[List[str]] = None,
                   where: Optional[Dict[str, Any]] = None,
                   order_by: Optional[str] = None,
                   as_dict: bool = False) -> Optional[Any]:
        """
        Выборка одной записи из таблицы
        
        Args:
            table: Имя таблицы
            columns: Список колонок для выборки (None = все колонки)
            where: Словарь условий WHERE
            order_by: Колонка для сортировки
            as_dict: Если True, возвращает словарь вместо кортежа
        
        Returns:
            Одна запись (кортеж или словарь) или None
        """
        results = self.select(table, columns, where, order_by, limit=1, as_dict=as_dict)
        return results[0] if results else None
    
    def select_by_id(self,
                     table: str,
                     id_value: Any,
                     id_column: str = 'id',
                     as_dict: bool = False) -> Optional[Any]:
        """
        Выборка записи по ID
        
        Args:
            table: Имя таблицы
            id_value: Значение ID
            id_column: Название колонки с ID (по умолчанию 'id')
            as_dict: Если True, возвращает словарь вместо кортежа
        
        Returns:
            Запись (кортеж или словарь) или None
        """
        return self.select_one(table, where={id_column: id_value}, as_dict=as_dict)
    
    # ==================== UPDATE методы ====================
    
    def update(self,
               table: str,
               data: Dict[str, Any],
               where: Dict[str, Any],
               returning: Optional[str] = None) -> List[Any]:
        """
        Обновление записей в таблице
        
        Args:
            table: Имя таблицы
            data: Словарь с данными для обновления
            where: Словарь условий WHERE
            returning: Колонка для возврата значений
        
        Returns:
            Список значений возвращаемой колонки или пустой список
        """
        if not data:
            raise ValueError("Данные для обновления не могут быть пустыми")
        if not where:
            raise ValueError("Условие WHERE обязательно для безопасности")
        
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        where_clause = ' AND '.join([f"{key} = %s" for key in where.keys()])
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + list(where.values())
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if returning:
                return [row[0] for row in cursor.fetchall()]
            return []
    
    def update_by_id(self,
                     table: str,
                     id_value: Any,
                     data: Dict[str, Any],
                     id_column: str = 'id',
                     returning: Optional[str] = None) -> Optional[Any]:
        """
        Обновление записи по ID
        
        Args:
            table: Имя таблицы
            id_value: Значение ID
            data: Словарь с данными для обновления
            id_column: Название колонки с ID (по умолчанию 'id')
            returning: Колонка для возврата значения
        
        Returns:
            Значение возвращаемой колонки или None
        """
        results = self.update(table, data, {id_column: id_value}, returning)
        return results[0] if results else None
    
    # ==================== DELETE методы ====================
    
    def delete(self,
               table: str,
               where: Dict[str, Any],
               returning: Optional[str] = None) -> List[Any]:
        """
        Удаление записей из таблицы
        
        Args:
            table: Имя таблицы
            where: Словарь условий WHERE (обязательно для безопасности)
            returning: Колонка для возврата значений
        
        Returns:
            Список значений возвращаемой колонки или пустой список
        """
        if not where:
            raise ValueError("Условие WHERE обязательно для безопасности")
        
        where_clause = ' AND '.join([f"{key} = %s" for key in where.keys()])
        params = list(where.values())
        
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if returning:
                return [row[0] for row in cursor.fetchall()]
            return []
    
    def delete_by_id(self,
                     table: str,
                     id_value: Any,
                     id_column: str = 'id',
                     returning: Optional[str] = None) -> Optional[Any]:
        """
        Удаление записи по ID
        
        Args:
            table: Имя таблицы
            id_value: Значение ID
            id_column: Название колонки с ID (по умолчанию 'id')
            returning: Колонка для возврата значения
        
        Returns:
            Значение возвращаемой колонки или None
        """
        results = self.delete(table, {id_column: id_value}, returning)
        return results[0] if results else None
    
    # ==================== Дополнительные методы ====================
    
    def execute(self,
                query: str,
                params: Optional[Tuple] = None,
                fetch: bool = False,
                as_dict: bool = False) -> Optional[List[Any]]:
        """
        Выполнение произвольного SQL запроса
        
        Args:
            query: SQL запрос
            params: Параметры для запроса (кортеж)
            fetch: Если True, возвращает результаты запроса
            as_dict: Если True, возвращает словари вместо кортежей
        
        Returns:
            Результаты запроса или None
        """
        with self.get_cursor(dict_cursor=as_dict) as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def execute_many(self,
                     query: str,
                     params_list: List[Tuple]) -> None:
        """
        Выполнение запроса с множественными параметрами
        
        Args:
            query: SQL запрос
            params_list: Список кортежей с параметрами
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
    
    def count(self,
              table: str,
              where: Optional[Dict[str, Any]] = None) -> int:
        """
        Подсчет количества записей в таблице
        
        Args:
            table: Имя таблицы
            where: Словарь условий WHERE
        
        Returns:
            Количество записей
        """
        query = f"SELECT COUNT(*) FROM {table}"
        params = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def exists(self,
               table: str,
               where: Dict[str, Any]) -> bool:
        """
        Проверка существования записи
        
        Args:
            table: Имя таблицы
            where: Словарь условий WHERE
        
        Returns:
            True если запись существует, False в противном случае
        """
        return self.count(table, where) > 0
    
    def _python_type_to_postgres(self, python_type: type, constraints: Optional[str] = None) -> str:
        """
        Преобразование типа данных Python в тип данных PostgreSQL
        
        Args:
            python_type: Тип данных Python (int, str, bool, datetime, date, time, float)
            constraints: Дополнительные ограничения (например, 'NOT NULL', 'UNIQUE', 'DEFAULT value')
        
        Returns:
            Строка с определением типа PostgreSQL
        
        Example:
            _python_type_to_postgres(int) -> 'INTEGER'
            _python_type_to_postgres(str, 'NOT NULL') -> 'VARCHAR(255) NOT NULL'
            _python_type_to_postgres(bool, 'DEFAULT TRUE') -> 'BOOLEAN DEFAULT TRUE'
        """
        type_mapping = {
            int: 'INTEGER',
            str: 'VARCHAR(255)',
            bool: 'BOOLEAN',
            float: 'REAL',
            datetime: 'TIMESTAMP',
            date: 'DATE',
            time: 'TIME',
        }
        
        # Обработка строковых типов для datetime, date, time
        if isinstance(python_type, str):
            str_type_mapping = {
                'date': 'DATE',
                'time': 'TIME',
                'datetime': 'TIMESTAMP',
            }
            postgres_type = str_type_mapping.get(python_type.lower(), type_mapping.get(python_type, 'VARCHAR(255)'))
        else:
            postgres_type = type_mapping.get(python_type, 'VARCHAR(255)')
        
        if constraints:
            return f"{postgres_type} {constraints}"
        return postgres_type
    
    def _generate_create_table_sql(self, table_name: str, schema: Dict[str, Any]) -> str:
        """
        Генерация SQL-запроса для создания таблицы
        
        Args:
            table_name: Имя таблицы
            schema: Словарь с описанием колонок таблицы
                    Ключ - имя колонки
                    Значение - может быть:
                    - строка с полным определением (например, 'SERIAL PRIMARY KEY')
                    - словарь с ключами: 'type', 'constraints', 'default', 'primary_key'
                    - тип Python (int, str, bool и т.д.) для автоматического определения
        
        Returns:
            SQL-запрос для создания таблицы
        
        Example:
            schema = {
                'id': 'SERIAL PRIMARY KEY',
                'name': {'type': str, 'constraints': 'NOT NULL'},
                'email': {'type': str, 'constraints': 'UNIQUE NOT NULL'},
                'is_active': {'type': bool, 'default': True}
            }
        """
        columns_def = []
        
        for column_name, column_def in schema.items():
            if isinstance(column_def, str):
                # Если передана строка напрямую, используем её как есть
                columns_def.append(f"{column_name} {column_def}")
            elif isinstance(column_def, dict):
                # Если передан словарь с описанием колонки
                col_type = column_def.get('type', str)
                constraints_parts = []
                
                # Определяем тип PostgreSQL
                if isinstance(col_type, str) and col_type.upper() in ['SERIAL', 'BIGSERIAL', 'INTEGER', 'VARCHAR', 'TEXT', 'BOOLEAN', 'TIMESTAMP', 'DATE', 'TIME']:
                    postgres_type = col_type
                else:
                    postgres_type = self._python_type_to_postgres(col_type).split()[0]
                
                # Добавляем ограничения размера для VARCHAR
                if 'size' in column_def and postgres_type.startswith('VARCHAR'):
                    postgres_type = f"VARCHAR({column_def['size']})"
                
                constraints_parts.append(postgres_type)
                
                # Добавляем PRIMARY KEY
                if column_def.get('primary_key', False):
                    constraints_parts.append('PRIMARY KEY')
                
                # Добавляем DEFAULT
                if 'default' in column_def:
                    default_value = column_def['default']
                    # Список PostgreSQL функций, которые не нужно брать в кавычки
                    postgres_functions = ['CURRENT_TIMESTAMP', 'CURRENT_DATE', 'CURRENT_TIME', 'NOW()', 'NOW']
                    
                    if isinstance(default_value, str):
                        # Если это функция PostgreSQL, не добавляем кавычки
                        if default_value.upper() in [f.upper() for f in postgres_functions] or default_value.endswith('()'):
                            constraints_parts.append(f"DEFAULT {default_value}")
                        else:
                            constraints_parts.append(f"DEFAULT '{default_value}'")
                    elif isinstance(default_value, bool):
                        constraints_parts.append(f"DEFAULT {str(default_value).upper()}")
                    else:
                        constraints_parts.append(f"DEFAULT {default_value}")
                
                # Добавляем дополнительные ограничения
                if 'constraints' in column_def:
                    constraints_parts.append(column_def['constraints'])
                
                columns_def.append(f"{column_name} {' '.join(constraints_parts)}")
            else:
                # Если передан только тип Python
                postgres_type = self._python_type_to_postgres(column_def)
                columns_def.append(f"{column_name} {postgres_type}")
        
        # Выносим разделитель в переменную, так как нельзя использовать \n внутри f-строки
        separator = ',\n    '
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {separator.join(columns_def)}\n);"
    
    def create_table_from_model(self, model, schema: Dict[str, Any]) -> bool:
        """
        Основная функция для создания таблицы из модели, если она не существует
        
        Args:
            model: Модуль модели (например, models.user)
                   Должен содержать константу TABLE_NAME с именем таблицы
            schema: Словарь с описанием колонок таблицы
                    Ключ - имя колонки
                    Значение может быть:
                    - строка с полным определением (например, 'SERIAL PRIMARY KEY')
                    - словарь с ключами: 'type', 'constraints', 'default', 'primary_key', 'size'
                    - тип Python (int, str, bool, datetime, date, time) для автоматического определения
        
        Returns:
            True если таблица создана или уже существует, False при ошибке
        
        Example:
            from models import user
            
            # Вариант 1: Строки с полным определением
            schema1 = {
                'id': 'SERIAL PRIMARY KEY',
                'name': 'VARCHAR(255) NOT NULL',
                'email': 'VARCHAR(255) UNIQUE NOT NULL'
            }
            
            # Вариант 2: Словари с описанием
            schema2 = {
                'id': {'type': 'SERIAL', 'primary_key': True},
                'name': {'type': str, 'constraints': 'NOT NULL', 'size': 255},
                'email': {'type': str, 'constraints': 'UNIQUE NOT NULL', 'size': 255},
                'is_active': {'type': bool, 'default': True}
            }
            
            # Вариант 3: Только типы Python (автоматическое определение)
            schema3 = {
                'id': 'SERIAL PRIMARY KEY',  # для специальных типов используем строки
                'name': str,
                'email': str,
                'is_active': bool
            }
            
            db.create_table_from_model(user, schema2)
        """
        # Получаем имя таблицы из модели
        table_name = getattr(model, 'TABLE_NAME', None)
        if not table_name:
            raise ValueError("Модель должна содержать константу TABLE_NAME")
        
        # Проверяем существование таблицы
        try:
            if not self.is_connected():
                self.connect()
            
            check_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """
            
            with self.get_cursor() as cursor:
                cursor.execute(check_query, (table_name,))
                exists = cursor.fetchone()[0]
            
            if exists:
                return True
            
            # Генерируем SQL-запрос
            create_query = self._generate_create_table_sql(table_name, schema)
            
            # Выполняем создание таблицы
            with self.get_cursor() as cursor:
                cursor.execute(create_query)
            
            return True
            
        except Exception as e:
            raise Exception(f"Ошибка при создании таблицы {table_name}: {e}")
    
    def get_user_totals(self, as_dict: bool = True) -> List[Any]:
        """
        Получение суммы заказов по каждому пользователю
        Использует LEFT JOIN для показа всех пользователей, даже без заказов
        Сортирует по сумме по убыванию
        
        Args:
            as_dict: Если True, возвращает словари вместо кортежей
        
        Returns:
            Список записей с информацией о пользователях и сумме их заказов
        """
        query = """
            SELECT 
                u.id,
                u.name,
                u.email,
                COALESCE(SUM(o.amount), 0) as total_amount
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id, u.name, u.email
            ORDER BY total_amount DESC
        """
        
        with self.get_cursor(dict_cursor=as_dict) as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие подключения при выходе из контекста"""
        self.disconnect()
    
    def __del__(self):
        """Закрытие подключения при удалении объекта"""
        self.disconnect()
