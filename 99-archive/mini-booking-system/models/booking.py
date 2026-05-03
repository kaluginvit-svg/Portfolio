"""
Функции для работы с бронированиями в мини-системе бронирования
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date, time, timedelta
from postgre_driver import PostgreSQLDriver

TABLE_NAME = 'bookings'

STATUS_PENDING = 'pending'
STATUS_CONFIRMED = 'confirmed'
STATUS_CANCELLED = 'cancelled'
STATUS_COMPLETED = 'completed'


def has_conflict(db: PostgreSQLDriver,
                table_id: int,
                booking_date: date,
                booking_time: time,
                duration_minutes: int,
                exclude_booking_id: Optional[int] = None) -> bool:
    """
    Проверка наличия конфликта бронирования (стол уже забронирован на это время)
    
    Args:
        db: Экземпляр PostgreSQLDriver
        table_id: ID стола
        booking_date: Дата бронирования
        booking_time: Время начала бронирования
        duration_minutes: Продолжительность в минутах
        exclude_booking_id: ID бронирования для исключения из проверки (при обновлении)
    
    Returns:
        True если есть конфликт (стол занят), False если свободен
    """
    # Получаем все активные бронирования стола на эту дату (confirmed и pending)
    # Исключаем cancelled и completed
    existing_bookings_confirmed = get_bookings_by_table(
        db,
        table_id,
        booking_date=booking_date,
        status=STATUS_CONFIRMED
    )
    existing_bookings_pending = get_bookings_by_table(
        db,
        table_id,
        booking_date=booking_date,
        status=STATUS_PENDING
    )
    # Объединяем списки
    existing_bookings = existing_bookings_confirmed + existing_bookings_pending
    
    # Вычисляем время начала и окончания нового бронирования
    booking_datetime = datetime.combine(booking_date, booking_time)
    end_datetime = booking_datetime + timedelta(minutes=duration_minutes)
    
    # Проверяем пересечения с существующими бронированиями
    for existing in existing_bookings:
        # Пропускаем текущее бронирование при обновлении
        if exclude_booking_id and existing.get('id') == exclude_booking_id:
            continue
        
        # Получаем время существующего бронирования
        existing_time_str = existing.get('booking_time')
        if isinstance(existing_time_str, str):
            # Обработка формата времени
            if len(existing_time_str.split(':')) == 2:
                existing_time_str += ':00'
            try:
                existing_time = time.fromisoformat(existing_time_str)
            except:
                continue
        else:
            existing_time = existing_time_str
        
        existing_duration = existing.get('duration_minutes', 120)
        existing_start = datetime.combine(booking_date, existing_time)
        existing_end = existing_start + timedelta(minutes=existing_duration)
        
        # Проверка пересечения интервалов
        # Интервалы пересекаются, если НЕ выполняется условие:
        # новый_конец <= существующий_начало ИЛИ новый_начало >= существующий_конец
        if not (end_datetime <= existing_start or booking_datetime >= existing_end):
            return True  # Есть пересечение - конфликт
    
    return False  # Конфликтов нет


def create_booking(db: PostgreSQLDriver, data: Dict[str, Any]) -> Optional[int]:
    """Создание нового бронирования"""
    booking_date = data.get('booking_date')
    if isinstance(booking_date, str):
        booking_date = date.fromisoformat(booking_date)
    
    booking_time = data.get('booking_time')
    if isinstance(booking_time, str):
        time_str = booking_time
        if len(time_str.split(':')) == 2:
            time_str += ':00'
        booking_time = time.fromisoformat(time_str)
    
    # Проверка конфликтов времени (только для подтвержденных бронирований)
    table_id = data.get('table_id')
    duration_minutes = data.get('duration_minutes', 120)
    status = data.get('status', STATUS_PENDING)
    
    # Проверяем конфликты для всех статусов кроме cancelled и completed
    if status not in [STATUS_CANCELLED, STATUS_COMPLETED]:
        if has_conflict(db, table_id, booking_date, booking_time, duration_minutes):
            raise ValueError("Стол уже забронирован на указанное время")
    
    booking_data = {
        'user_id': data.get('user_id'),
        'table_id': table_id,
        'booking_date': booking_date.isoformat() if isinstance(booking_date, date) else booking_date,
        'booking_time': booking_time.isoformat() if isinstance(booking_time, time) else booking_time,
        'duration_minutes': duration_minutes,
        'guests_count': data.get('guests_count', 2),
        'status': status,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    if 'notes' in data:
        booking_data['notes'] = data['notes']
    
    return db.insert(table=TABLE_NAME, data=booking_data, returning='id')


def get_booking_by_id(db: PostgreSQLDriver, booking_id: int) -> Optional[Dict[str, Any]]:
    """Получение бронирования по ID"""
    return db.select_by_id(table=TABLE_NAME, id_value=booking_id, as_dict=True)


def get_bookings_by_user(db: PostgreSQLDriver,
                         user_id: int,
                         status: Optional[str] = None,
                         limit: Optional[int] = None,
                         offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """Получение всех бронирований пользователя"""
    where = {'user_id': user_id}
    if status:
        where['status'] = status
    
    return db.select(
        table=TABLE_NAME,
        where=where,
        order_by='booking_date DESC, booking_time DESC',
        limit=limit,
        offset=offset,
        as_dict=True
    )


def get_bookings_by_table(db: PostgreSQLDriver,
                          table_id: int,
                          booking_date: Optional[date] = None,
                          status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Получение всех бронирований стола"""
    where = {'table_id': table_id}
    if booking_date:
        where['booking_date'] = booking_date.isoformat() if isinstance(booking_date, date) else booking_date
    if status:
        where['status'] = status
    
    return db.select(
        table=TABLE_NAME,
        where=where,
        order_by='booking_date ASC, booking_time ASC',
        as_dict=True
    )


def get_all_bookings(db: PostgreSQLDriver,
                     status: Optional[str] = None,
                     booking_date: Optional[date] = None,
                     limit: Optional[int] = None,
                     offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """Получение списка всех бронирований"""
    where = {}
    if status:
        where['status'] = status
    if booking_date:
        where['booking_date'] = booking_date.isoformat() if isinstance(booking_date, date) else booking_date
    
    return db.select(
        table=TABLE_NAME,
        where=where if where else None,
        order_by='booking_date DESC, booking_time DESC',
        limit=limit,
        offset=offset,
        as_dict=True
    )


def update_booking(db: PostgreSQLDriver, booking_id: int, data: Dict[str, Any]) -> bool:
    """Обновление данных бронирования"""
    # Получаем текущее бронирование для проверки конфликтов
    existing_booking = get_booking_by_id(db, booking_id)
    if not existing_booking:
        raise ValueError(f"Бронирование с ID {booking_id} не найдено")
    
    # Объединяем существующие данные с новыми
    full_data = existing_booking.copy()
    full_data.update(data)
    
    # Проверка конфликтов, если изменились дата, время, стол или статус
    if any(key in data for key in ['booking_date', 'booking_time', 'table_id', 'duration_minutes', 'status']):
        booking_date = full_data.get('booking_date')
        if isinstance(booking_date, str):
            booking_date = date.fromisoformat(booking_date)
        
        booking_time = full_data.get('booking_time')
        if isinstance(booking_time, str):
            time_str = booking_time
            if len(time_str.split(':')) == 2:
                time_str += ':00'
            booking_time = time.fromisoformat(time_str)
        
        table_id = full_data.get('table_id')
        duration_minutes = full_data.get('duration_minutes', 120)
        status = full_data.get('status', STATUS_PENDING)
        
        # Проверяем конфликты для всех статусов кроме cancelled и completed
        if status not in [STATUS_CANCELLED, STATUS_COMPLETED]:
            if has_conflict(db, table_id, booking_date, booking_time, duration_minutes, exclude_booking_id=booking_id):
                raise ValueError("Стол уже забронирован на указанное время")
    
    data['updated_at'] = datetime.now()
    db.update_by_id(table=TABLE_NAME, id_value=booking_id, data=data)
    return True


def delete_booking(db: PostgreSQLDriver, booking_id: int) -> bool:
    """Удаление бронирования"""
    db.delete_by_id(table=TABLE_NAME, id_value=booking_id)
    return True
