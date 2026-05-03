"""
Сервис для управления задачами
"""

from datetime import date
from typing import List, Optional

from models import User, Project, Task, TaskStatus


class TaskService:
    """Сервис для управления жизненным циклом задач"""
    
    def __init__(self):
        self.tasks: List[Task] = []
    
    def create_task(
        self,
        user: User,
        project: Project,
        project_service: 'ProjectService',
        title: str,
        description: Optional[str] = None,
        due_date: Optional[date] = None
    ) -> Optional[Task]:
        """
        Создает новую задачу в проекте.
        Проверяет, является ли user участником проекта.
        """
        # Проверка прав пользователя
        if not project_service._is_member(user.id, project.id):
            print(f"\n✗ Отказано в доступе. {user.username} не является участником проекта '{project.name}'")
            return None
        
        # Создание задачи
        task = Task(
            title=title,
            project_id=project.id,
            description=description,
            due_date=due_date
        )
        self.tasks.append(task)
        
        print(f"\n✓ Задача '{title}' создана в проекте '{project.name}'")
        print(f"  ID задачи: {task.id}")
        return task
    
    def assign_task(
        self,
        acting_user: User,
        task: Task,
        target_user: User,
        project_service: 'ProjectService'
    ) -> bool:
        """
        Назначает пользователя ответственным за задачу.
        Проверяет права acting_user и членство target_user в проекте.
        """
        # Проверка прав acting_user (должен быть участником проекта)
        if not project_service._is_member(acting_user.id, task.project_id):
            print(f"\n✗ Отказано в доступе. {acting_user.username} не является участником проекта")
            return False
        
        # Проверка, что target_user является участником проекта
        if not project_service._is_member(target_user.id, task.project_id):
            print(f"\n✗ Невозможно назначить. {target_user.username} не является участником проекта")
            return False
        
        # Назначение пользователя
        task.assignee_id = target_user.id
        print(f"\n✓ Пользователь {target_user.username} назначен ответственным за задачу '{task.title}'")
        return True
    
    def change_task_status(
        self,
        user: User,
        task: Task,
        new_status: TaskStatus,
        project_service: 'ProjectService'
    ) -> bool:
        """
        Изменяет статус задачи.
        Проверяет права пользователя.
        """
        if not project_service._is_member(user.id, task.project_id):
            print(f"\n✗ Отказано в доступе. {user.username} не является участником проекта")
            return False
        
        old_status = task.status
        task.status = new_status
        print(f"\n✓ Статус задачи '{task.title}' изменен: {old_status.value} → {new_status.value}")
        return True
