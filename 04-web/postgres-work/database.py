"""
Модуль для работы с базой данных PostgreSQL.
Обеспечивает подключение к БД и получение информации о структуре таблиц.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных PostgreSQL."""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        Инициализация подключения к базе данных.
        
        Args:
            host: Хост базы данных
            port: Порт базы данных
            database: Имя базы данных
            user: Имя пользователя
            password: Пароль
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
    
    def connect(self) -> bool:
        """
        Установка подключения к базе данных.
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info("Успешное подключение к базе данных")
            return True
        except psycopg2.Error as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            return False
    
    def disconnect(self):
        """Закрытие подключения к базе данных."""
        if self.connection:
            self.connection.close()
            logger.info("Подключение к базе данных закрыто")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Выполнение SQL запроса с возвратом результатов.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса (опционально)
            
        Returns:
            Список словарей с результатами запроса
        """
        if not self.connection:
            logger.error("Нет подключения к базе данных")
            return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []
        except psycopg2.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            return []
    
    def execute_command(self, command: str, params: Optional[tuple] = None) -> bool:
        """
        Выполнение SQL команды без возврата результатов (INSERT, UPDATE, DELETE).
        
        Args:
            command: SQL команда
            params: Параметры для команды (опционально)
            
        Returns:
            True если команда выполнена успешно, False в противном случае
        """
        if not self.connection:
            logger.error("Нет подключения к базе данных")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(command, params)
                self.connection.commit()
                return True
        except psycopg2.Error as e:
            logger.error(f"Ошибка выполнения команды: {e}")
            self.connection.rollback()
            return False
    
    def get_tables(self) -> List[str]:
        """
        Получение списка всех таблиц в базе данных.
        
        Returns:
            Список имен таблиц
        """
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        results = self.execute_query(query)
        return [row['table_name'] for row in results]
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Получение информации о колонках таблицы.
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            Список словарей с информацией о колонках
        """
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = %s
            ORDER BY ordinal_position;
        """
        return self.execute_query(query, (table_name,))
    
    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """
        Получение полной структуры таблицы.
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            Словарь с информацией о структуре таблицы
        """
        columns = self.get_table_columns(table_name)
        return {
            'table_name': table_name,
            'columns': columns
        }
    
    def test_connection(self) -> bool:
        """
        Проверка подключения к базе данных.
        
        Returns:
            True если подключение работает, False в противном случае
        """
        try:
            result = self.execute_query("SELECT 1")
            return len(result) > 0
        except Exception as e:
            logger.error(f"Ошибка проверки подключения: {e}")
            return False
    
    def insert_form_data(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        Вставка данных анкеты в таблицу.
        
        Args:
            table_name: Имя таблицы
            data: Словарь с данными для вставки (ключ - имя колонки, значение - значение)
            
        Returns:
            True если данные успешно вставлены, False в противном случае
        """
        if not data:
            logger.error("Нет данных для вставки")
            return False
        
        # Формируем список колонок и значений
        # Экранируем имена колонок для безопасности
        columns = list(data.keys())
        placeholders = ', '.join(['%s'] * len(columns))
        # Используем двойные кавычки для экранирования имен колонок в PostgreSQL
        column_names = ', '.join([f'"{col}"' for col in columns])
        values = tuple(data.values())
        
        query = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
        
        return self.execute_command(query, values)
