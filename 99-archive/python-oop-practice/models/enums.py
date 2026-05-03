"""
Перечисления (Enums) для системы управления задачами
"""

from enum import Enum


class TaskStatus(Enum):
    """Статусы задач"""
    TODO = 'ToDo'
    IN_PROGRESS = 'InProgress'
    DONE = 'Done'


class ProjectRole(Enum):
    """Роли пользователей в проекте"""
    ADMIN = 'Admin'
    MEMBER = 'Member'
    GUEST = 'Guest'
