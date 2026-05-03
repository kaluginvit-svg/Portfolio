"""
Сервис для управления проектами
"""

from typing import List, Optional
from uuid import UUID

from models import User, Project, Membership, ProjectRole, Task


class ProjectService:
    """Сервис для управления проектами, участниками и правами доступа"""
    
    def __init__(self):
        self.projects: List[Project] = []
        self.memberships: List[Membership] = []
    
    def create_project(self, user: User, name: str, description: str = "") -> Project:
        """
        Создает новый проект.
        Назначает user его владельцем и добавляет в Membership с ролью Admin.
        """
        project = Project(name=name, description=description, owner_id=user.id)
        self.projects.append(project)
        
        # Добавляем создателя как администратора
        membership = Membership(
            user_id=user.id,
            project_id=project.id,
            role=ProjectRole.ADMIN
        )
        self.memberships.append(membership)
        
        print(f"\n✓ Проект '{name}' создан пользователем {user.username}")
        print(f"  ID проекта: {project.id}")
        return project
    
    def add_user_to_project(
        self,
        acting_user: User,
        project: Project,
        target_user: User,
        role: ProjectRole
    ) -> bool:
        """
        Добавляет пользователя в проект с определенной ролью.
        Проверяет, имеет ли acting_user права администратора.
        """
        # Проверка прав acting_user
        if not self._is_admin(acting_user.id, project.id):
            print(f"\n✗ Отказано в доступе. {acting_user.username} не является администратором проекта '{project.name}'")
            return False
        
        # Проверка, не состоит ли пользователь уже в проекте
        if self._is_member(target_user.id, project.id):
            print(f"\n✗ Пользователь {target_user.username} уже состоит в проекте '{project.name}'")
            return False
        
        # Добавление пользователя
        membership = Membership(
            user_id=target_user.id,
            project_id=project.id,
            role=role
        )
        self.memberships.append(membership)
        
        print(f"\n✓ Пользователь {target_user.username} добавлен в проект '{project.name}' с ролью {role.value}")
        return True
    
    def get_project_tasks(self, user: User, project: Project, task_service: 'TaskService') -> List[Task]:
        """
        Возвращает список задач проекта.
        Проверяет, имеет ли user доступ к проекту.
        """
        if not self._is_member(user.id, project.id):
            print(f"\n✗ Отказано в доступе. {user.username} не является участником проекта '{project.name}'")
            return []
        
        tasks = [task for task in task_service.tasks if task.project_id == project.id]
        print(f"\n✓ Получен список задач проекта '{project.name}' ({len(tasks)} задач)")
        return tasks
    
    def get_user_role(self, user_id: UUID, project_id: UUID) -> Optional[ProjectRole]:
        """Возвращает роль пользователя в проекте"""
        for membership in self.memberships:
            if membership.user_id == user_id and membership.project_id == project_id:
                return membership.role
        return None
    
    def _is_admin(self, user_id: UUID, project_id: UUID) -> bool:
        """Проверяет, является ли пользователь администратором проекта"""
        role = self.get_user_role(user_id, project_id)
        return role == ProjectRole.ADMIN
    
    def _is_member(self, user_id: UUID, project_id: UUID) -> bool:
        """Проверяет, является ли пользователь участником проекта"""
        return self.get_user_role(user_id, project_id) is not None
