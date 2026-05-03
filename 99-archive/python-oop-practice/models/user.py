"""
Модель пользователя
"""

from datetime import datetime
from uuid import uuid4, UUID


class User:
    """Пользователь системы"""
    
    def __init__(self, username: str, email: str):
        self.id: UUID = uuid4()
        self.username: str = username
        self.email: str = email
        self.created_at: datetime = datetime.now()
    
    def update_profile(self, new_username: str) -> None:
        """Изменяет данные профиля пользователя"""
        self.username = new_username
        print(f"✓ Профиль обновлен. Новое имя пользователя: {self.username}")
    
    def __str__(self) -> str:
        return f"User(username='{self.username}', email='{self.email}')"
    
    def __repr__(self) -> str:
        return self.__str__()
