"""
Учебный файл-совместимость: те же имена, что раньше.

Предпочтительный импорт для нового кода: `from api import add_user, store_password`.
"""
from api import add_user, store_password

__all__ = ["add_user", "store_password"]
