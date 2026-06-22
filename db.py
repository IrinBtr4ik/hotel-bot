# db.py

import pymssql
from db_config import DB_CONFIG
from datetime import datetime

# =============================================
# ПОДКЛЮЧЕНИЕ К БД
# =============================================

def get_connection():
    """Создает и возвращает подключение к MS SQL"""
    try:
        conn = pymssql.connect(
            server=DB_CONFIG['server'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            port=DB_CONFIG.get('port', 1433),
            charset='utf-8'
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return None

def execute_query(query, params=None):
    """Выполняет SQL-запрос и возвращает результат"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(as_dict=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Если это SELECT — возвращаем результат
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
            conn.close()
            return result
        
        # Если это INSERT/UPDATE/DELETE — коммитим
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка выполнения запроса: {e}")
        conn.close()
        return None

# =============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ГОСТЯМИ
# =============================================

def get_guest_by_telegram_id(telegram_id):
    """Найти гостя по Telegram ID"""
    query = """
        SELECT GuestID, TelegramID, FullName, Phone, Email, CreatedAt
        FROM Guests
        WHERE TelegramID = %s
    """
    result = execute_query(query, (telegram_id,))
    if result and len(result) > 0:
        return result[0]
    return None

def create_guest(telegram_id, full_name, phone, email=None):
    """Создать нового гостя"""
    query = """
        INSERT INTO Guests (TelegramID, FullName, Phone, Email, CreatedAt)
        VALUES (%s, %s, %s, %s, GETDATE())
    """
    params = (telegram_id, full_name, phone, email)
    success = execute_query(query, params)
    
    if success:
        # Получаем ID созданного гостя
        query_id = "SELECT SCOPE_IDENTITY() AS GuestID"
        result = execute_query(query_id)
        if result and len(result) > 0:
            return result[0]['GuestID']
    return None

# =============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С НОМЕРАМИ
# =============================================

def get_room_by_number(room_number):
    """Получить информацию о номере по его номеру"""
    query = """
        SELECT RoomID, RoomNumber, RoomName, Category, PricePerNight, MaxCapacity, IsActive
        FROM Rooms
        WHERE RoomNumber = %s AND IsActive = 1
    """
    result = execute_query(query, (room_number,))
    if result and len(result) > 0:
        return result[0]
    return None

def get_all_rooms():
    """Получить все активные номера"""
    query = """
        SELECT RoomID, RoomNumber, RoomName, Category, PricePerNight, MaxCapacity
        FROM Rooms
        WHERE IsActive = 1
        ORDER BY RoomNumber
    """
    return execute_query(query) or []

def search_free_rooms(check_in_date, check_out_date):
    """Поиск свободных номеров на указанные даты"""
    query = """
        SELECT 
            r.RoomNumber,
            r.RoomName,
            r.Category,
            r.PricePerNight,
            r.MaxCapacity
        FROM Rooms r
        WHERE r.IsActive = 1
        AND NOT EXISTS (
            SELECT 1
            FROM Bookings b
            WHERE b.RoomID = r.RoomID
            AND b.Status IN ('Подтверждено', 'Активно')
            AND (
                (b.CheckInDate <= %s AND b.CheckOutDate >= %s)
                OR (b.CheckInDate <= %s AND b.CheckOutDate >= %s)
                OR (b.CheckInDate >= %s AND b.CheckOutDate <= %s)
            )
        )
    """
    params = (check_out_date, check_in_date, check_out_date, check_in_date, check_in_date, check_out_date)
    return execute_query(query, params) or []

# =============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БРОНИРОВАНИЯМИ
# =============================================

def create_booking(guest_id, room_id, check_in_date, check_out_date, total_price):
    """Создать новое бронирование"""
    query = """
        INSERT INTO Bookings (GuestID, RoomID, CheckInDate, CheckOutDate, TotalPrice, Status, Source, CreatedAt)
        VALUES (%s, %s, %s, %s, %s, 'Подтверждено', 'Telegram Bot', GETDATE())
    """
    params = (guest_id, room_id, check_in_date, check_out_date, total_price)
    success = execute_query(query, params)
    
    if success:
        query_id = "SELECT SCOPE_IDENTITY() AS BookingID"
        result = execute_query(query_id)
        if result and len(result) > 0:
            return result[0]['BookingID']
    return None

def get_user_bookings(telegram_id):
    """Получить все бронирования пользователя"""
    query = """
        SELECT 
            b.BookingID,
            r.RoomNumber,
            r.RoomName,
            b.CheckInDate,
            b.CheckOutDate,
            b.TotalPrice,
            b.Status,
            b.CreatedAt
        FROM Bookings b
        JOIN Rooms r ON b.RoomID = r.RoomID
        JOIN Guests g ON b.GuestID = g.GuestID
        WHERE g.TelegramID = %s
        ORDER BY b.CreatedAt DESC
    """
    return execute_query(query, (telegram_id,)) or []

def cancel_booking(booking_id, telegram_id):
    """Отменить бронирование (только если оно принадлежит пользователю)"""
    query = """
        UPDATE b
        SET b.Status = 'Отменено'
        FROM Bookings b
        JOIN Guests g ON b.GuestID = g.GuestID
        WHERE b.BookingID = %s AND g.TelegramID = %s
    """
    return execute_query(query, (booking_id, telegram_id))

# =============================================
# ФУНКЦИЯ ДЛЯ ПРОВЕРКИ ПОДКЛЮЧЕНИЯ
# =============================================

def test_connection():
    """Проверяет подключение к БД"""
    conn = get_connection()
    if conn:
        print("✅ Подключение к MS SQL установлено успешно!")
        conn.close()
        return True
    else:
        print("❌ НЕ УДАЛОСЬ подключиться к MS SQL!")
        return False
