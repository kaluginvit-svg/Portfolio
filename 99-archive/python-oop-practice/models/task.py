"""
Модель задачи
"""

from datetime import datetime, date
from typing import Optional
from uuid import uuid4, UUID

from models.enums import TaskStatus


class Task:
    """Задача - конкретная единица работы внутри проекта"""
    
    def __init__(
        self,
        title: str,
        project_id: UUID,
        description: Optional[str] = None,
        due_date: Optional[date] = None,
        assignee_id: Optional[UUID] = None
    ):
        self.id: UUID = uuid4()
        self.title: str = title
        self.description: Optional[str] = description
        self.status: TaskStatus = TaskStatus.TODO
        self.due_date: Optional[date] = due_date
        self.project_id: UUID = project_id
        self.assignee_id: Optional[UUID] = assignee_id
        self.created_at: datetime = datetime.now()
    
    def mark_as_done(self) -> None:
        """Устанавливает статус 'Done'"""
        self.status = TaskStatus.DONE
        print(f"✓ Задача '{self.title}' отмечена как выполненная")
    
    def reopen(self) -> None:
        """Устанавливает статус 'ToDo'"""
        self.status = TaskStatus.TODO
        print(f"✓ Задача '{self.title}' открыта заново")
    
    def set_due_date(self, new_date: date) -> None:
        """Изменяет срок выполнения"""
        self.due_date = new_date
        print(f"✓ Срок выполнения задачи '{self.title}' установлен на {new_date}")
    
    def __str__(self) -> str:
        assignee = f", assignee_id={str(self.assignee_id)[:8]}..." if self.assignee_id else ""
        return f"Task(title='{self.title}', status={self.status.value}{assignee})"
    
    def __repr__(self) -> str:
        return self.__str__()
