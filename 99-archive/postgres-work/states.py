"""
Модуль для управления состояниями пользователей (FSM).
Хранит промежуточные данные анкеты во время заполнения.
"""

from enum import Enum
from typing import Dict, Optional
from datetime import datetime


class FormState(Enum):
    """Состояния процесса заполнения анкеты."""
    IDLE = "idle"  # Бездействие
    WAITING_SERIAL = "waiting_serial"  # Ожидание названия сериала
    WAITING_DIRECTOR = "waiting_director"  # Ожидание режиссера
    WAITING_YEAR = "waiting_year"  # Ожидание года
    WAITING_STATUS = "waiting_status"  # Ожидание статуса
    WAITING_RATING = "waiting_rating"  # Ожидание рейтинга


class UserStates:
    """Класс для управления состояниями пользователей."""
    
    def __init__(self):
        """Инициализация хранилища состояний."""
        self.states: Dict[int, FormState] = {}  # user_id -> state
        self.form_data: Dict[int, Dict[str, str]] = {}  # user_id -> данные формы
    
    def set_state(self, user_id: int, state: FormState):
        """
        Установка состояния для пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            state: Состояние формы
        """
        self.states[user_id] = state
    
    def get_state(self, user_id: int) -> Optional[FormState]:
        """
        Получение текущего состояния пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Текущее состояние или None
        """
        return self.states.get(user_id)
    
    def reset_state(self, user_id: int):
        """
        Сброс состояния пользователя.
        
        Args:
            user_id: ID пользователя Telegram
        """
        self.states.pop(user_id, None)
        self.form_data.pop(user_id, None)
    
    def set_form_data(self, user_id: int, key: str, value: str):
        """
        Сохранение данных формы пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            key: Ключ данных
            value: Значение данных
        """
        if user_id not in self.form_data:
            self.form_data[user_id] = {}
        self.form_data[user_id][key] = value
    
    def get_form_data(self, user_id: int) -> Dict[str, str]:
        """
        Получение всех данных формы пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Словарь с данными формы
        """
        return self.form_data.get(user_id, {})
    
    def clear_form_data(self, user_id: int):
        """
        Очистка данных формы пользователя.
        
        Args:
            user_id: ID пользователя Telegram
        """
        self.form_data.pop(user_id, None)


def validate_date_format(date_str: str) -> Optional[datetime]:
    """
    Валидация формата даты (01.01.2001).
    
    Args:
        date_str: Строка с датой в формате DD.MM.YYYY
        
    Returns:
        Объект datetime если дата валидна, None в противном случае
    """
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        return None


def format_date_for_db(date_obj: datetime) -> str:
    """
    Преобразование даты в формат для базы данных (YYYY-MM-DD).
    
    Args:
        date_obj: Объект datetime
        
    Returns:
        Строка с датой в формате YYYY-MM-DD
    """
    return date_obj.strftime("%Y-%m-%d")
