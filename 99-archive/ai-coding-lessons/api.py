"""
Публичный API: единственная точка для вызовов из приложения, тестов или HTTP-слоя.

Реализация спрятана в users_repository и password_storage;
при появлении FastAPI/Flask маршруты только вызывают функции отсюда.
"""
from typing import Optional

from password_storage import append_password_hash
from users_repository import insert_user


def add_user(name: str, tags: Optional[list] = None) -> int:
    """Добавляет пользователя в локальную базу SQLite. Возвращает id (int)."""
    return insert_user(name, tags)


def store_password(user_id: int, password: str) -> None:
    """Сохраняет пароль в виде PBKDF2-SHA256 (соль + итерации в строке)."""
    append_password_hash(user_id, password)


__all__ = ["add_user", "store_password"]
