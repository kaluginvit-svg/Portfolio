"""
Модель членства в проекте
"""

from uuid import UUID

from models.enums import ProjectRole


class Membership:
    """Членство в проекте - связь между пользователем и проектом с определенной ролью"""
    
    def __init__(self, user_id: UUID, project_id: UUID, role: ProjectRole):
        self.user_id: UUID = user_id
        self.project_id: UUID = project_id
        self.role: ProjectRole = role
    
    def __str__(self) -> str:
        return f"Membership(user_id={str(self.user_id)[:8]}..., project_id={str(self.project_id)[:8]}..., role={self.role.value})"
    
    def __repr__(self) -> str:
        return self.__str__()
