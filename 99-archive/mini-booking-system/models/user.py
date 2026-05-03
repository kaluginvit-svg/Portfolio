"""
Функции для работы с пользователями в мини-системе бронирования
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from postgre_driver import PostgreSQLDriver

TABLE_NAME = 'users'


def create_user(db: PostgreSQLDriver, data: Dict[str, Any]) -> Optional[int]:
    """Создание нового пользователя"""
    user_data = {
        'name': data.get('name'),
        'email': data.get('email'),
        'phone': data.get('phone'),
        'role': data.get('role', 'client'),
        'is_active': data.get('is_active', True),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    if 'password_hash' in data:
        user_data['password_hash'] = data['password_hash']
    
    return db.insert(table=TABLE_NAME, data=user_data, returning='id')


def get_user_by_id(db: PostgreSQLDriver, user_id: int) -> Optional[Dict[str, Any]]:
    """Получение пользователя по ID"""
    return db.select_by_id(table=TABLE_NAME, id_value=user_id, as_dict=True)


def get_user_by_email(db: PostgreSQLDriver, email: str) -> Optional[Dict[str, Any]]:
    """Получение пользователя по email"""
    return db.select_one(table=TABLE_NAME, where={'email': email}, as_dict=True)


def get_all_users(db: PostgreSQLDriver,
                 active_only: bool = False,
                 role: Optional[str] = None,
                 limit: Optional[int] = None,
                 offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """Получение списка всех пользователей"""
    where = {}
    if active_only:
        where['is_active'] = True
    if role:
        where['role'] = role
    
    return db.select(
        table=TABLE_NAME,
        where=where if where else None,
        order_by='created_at DESC',
        limit=limit,
        offset=offset,
        as_dict=True
    )


def update_user(db: PostgreSQLDriver, user_id: int, data: Dict[str, Any]) -> bool:
    """Обновление данных пользователя"""
    data['updated_at'] = datetime.now()
    db.update_by_id(table=TABLE_NAME, id_value=user_id, data=data)
    return True


def delete_user(db: PostgreSQLDriver, user_id: int) -> bool:
    """Удаление пользователя"""
    db.delete_by_id(table=TABLE_NAME, id_value=user_id)
    return True
