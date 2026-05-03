"""
Сервисы для системы управления задачами
"""

from services.project_service import ProjectService
from services.task_service import TaskService

__all__ = [
    'ProjectService',
    'TaskService',
]
