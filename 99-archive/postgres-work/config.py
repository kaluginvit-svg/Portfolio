"""
Модуль для управления конфигурацией приложения.
Загружает настройки из переменных окружения.
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации приложения."""
    
    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # Настройки базы данных PostgreSQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', '')
    DB_USER = os.getenv('DB_USER', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Проверка наличия всех необходимых параметров конфигурации.
        
        Returns:
            True если все параметры заданы, False в противном случае
        """
        required_params = [
            cls.TELEGRAM_BOT_TOKEN,
            cls.DB_NAME,
            cls.DB_USER,
            cls.DB_PASSWORD
        ]
        return all(required_params)
