"""
Модель проекта
"""

from datetime import datetime
from uuid import uuid4, UUID


class Project:
    """Проект - логическая группа для объединения задач"""
    
    def __init__(self, name: str, description: str, owner_id: UUID):
        self.id: UUID = uuid4()
        self.name: str = name
        self.description: str = description
        self.owner_id: UUID = owner_id
        self.created_at: datetime = datetime.now()
        self.is_archived: bool = False
    
    def archive(self) -> None:
        """Архивирует проект, делая его недоступным для изменений"""
        self.is_archived = True
        print(f"✓ Проект '{self.name}' заархивирован")
    
    def change_name(self, new_name: str) -> None:
        """Меняет название проекта"""
        if self.is_archived:
            print(f"✗ Невозможно изменить название. Проект '{self.name}' заархивирован")
            return
        
        old_name = self.name
        self.name = new_name
        print(f"✓ Название проекта изменено: '{old_name}' → '{self.name}'")
    
    def __str__(self) -> str:
        status = " [ARCHIVED]" if self.is_archived else ""
        return f"Project(name='{self.name}'{status})"
    
    def __repr__(self) -> str:
        return self.__str__()
