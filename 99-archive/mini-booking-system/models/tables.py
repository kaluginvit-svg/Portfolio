"""
Функции для работы со столами в мини-системе бронирования
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from postgre_driver import PostgreSQLDriver

TABLE_NAME = 'restaurant_tables'


def create_table(db: PostgreSQLDriver, data: Dict[str, Any]) -> Optional[int]:
    """Создание нового стола"""
    table_data = {
        'table_number': data.get('table_number'),
        'capacity': data.get('capacity', 2),
        'is_available': data.get('is_available', True),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    if 'description' in data:
        table_data['description'] = data['description']
    if 'location' in data:
        table_data['location'] = data['location']
    
    return db.insert(table=TABLE_NAME, data=table_data, returning='id')


def get_table_by_id(db: PostgreSQLDriver, table_id: int) -> Optional[Dict[str, Any]]:
    """Получение стола по ID"""
    return db.select_by_id(table=TABLE_NAME, id_value=table_id, as_dict=True)


def get_table_by_number(db: PostgreSQLDriver, table_number: str) -> Optional[Dict[str, Any]]:
    """Получение стола по номеру"""
    return db.select_one(table=TABLE_NAME, where={'table_number': table_number}, as_dict=True)


def get_all_tables(db: PostgreSQLDriver,
                   available_only: bool = False,
                   min_capacity: Optional[int] = None,
                   location: Optional[str] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """Получение списка всех столов"""
    where = {}
    if available_only:
        where['is_available'] = True
    if location:
        where['location'] = location
    
    query = f"SELECT * FROM {TABLE_NAME}"
    conditions = []
    params = []
    
    if available_only:
        conditions.append("is_available = %s")
        params.append(True)
    if min_capacity:
        conditions.append("capacity >= %s")
        params.append(min_capacity)
    if location:
        conditions.append("location = %s")
        params.append(location)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY table_number ASC"
    if limit:
        query += f" LIMIT {limit}"
    if offset:
        query += f" OFFSET {offset}"
    
    if min_capacity:
        return db.execute(query, tuple(params) if params else None, fetch=True, as_dict=True)
    else:
        return db.select(
            table=TABLE_NAME,
            where=where if where else None,
            order_by='table_number ASC',
            limit=limit,
            offset=offset,
            as_dict=True
        )


def update_table(db: PostgreSQLDriver, table_id: int, data: Dict[str, Any]) -> bool:
    """Обновление данных стола"""
    data['updated_at'] = datetime.now()
    db.update_by_id(table=TABLE_NAME, id_value=table_id, data=data)
    return True


def delete_table(db: PostgreSQLDriver, table_id: int) -> bool:
    """Удаление стола"""
    db.delete_by_id(table=TABLE_NAME, id_value=table_id)
    return True
