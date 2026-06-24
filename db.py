# db.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'database.db')

def get_connection():
    """Создает подключение к SQLite"""
    try:
        # Создаем папку data, если её нет
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Чтобы можно было обращаться по именам колонок
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None

def create_tables():
    """Создает таблицы, если их нет"""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Создаем таблицу гостей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guests (
            guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Создаем таблицу номеров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            max_capacity INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Создаем таблицу бронирований
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            check_in_date TEXT NOT NULL,
            check_out_date TEXT NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'Подтверждено',
            source TEXT DEFAULT 'Telegram Bot',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (guest_id) REFERENCES guests(guest_id),
            FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Таблицы созданы (если их не было)")

def init_rooms():
    """Добавляет тестовые номера, если их нет"""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Проверяем, есть ли номера
    cursor.execute("SELECT COUNT(*) FROM rooms")
    count = cursor.fetchone()[0]
    
    if count == 0:
        rooms = [
            ('101', 'Одноместный эконом', 'Эконом', 2500, 1),
            ('102', 'Двухместный эконом', 'Эконом', 3000, 2),
            ('103', 'Эконом с видом на город', 'Эконом', 3200, 2),
            ('201', 'Стандарт с видом на город', 'Стандарт', 4500, 2),
            ('202', 'Стандарт с видом на море', 'Стандарт', 5500, 3),
            ('203', 'Семейный стандарт', 'Стандарт', 6000, 4),
            ('301', 'Люкс с джакузи', 'Люкс', 8500, 2),
            ('302', 'Люкс с террасой', 'Люкс', 9500, 3),
            ('401', 'Президентский люкс', 'Президентский', 15000, 4)
        ]
        cursor.executemany('''
            INSERT INTO rooms (room_number, room_name, category, price_per_night, max_capacity)
            VALUES (?, ?, ?, ?, ?)
        ''', rooms)
        conn.commit()
        print("✅ Добавлены тестовые номера")
    
    conn.close()


# Функции для работы с БД
def get_guest_by_telegram_id(telegram_id):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guests WHERE telegram_id = ?", (telegram_id,))
    guest = cursor.fetchone()
    conn.close()
    return guest

def create_guest(telegram_id, full_name, phone, email=None):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO guests (telegram_id, full_name, phone, email)
            VALUES (?, ?, ?, ?)
        ''', (telegram_id, full_name, phone, email))
        conn.commit()
        guest_id = cursor.lastrowid
        conn.close()
        return guest_id
    except Exception as e:
        print(f"❌ Ошибка создания гостя: {e}")
        conn.close()
        return None

def get_room_by_number(room_number):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms WHERE room_number = ? AND is_active = 1", (room_number,))
    room = cursor.fetchone()
    conn.close()
    return room

def get_all_rooms():
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms WHERE is_active = 1 ORDER BY room_number")
    rooms = cursor.fetchall()
    conn.close()
    return rooms

def search_free_rooms(check_in_date, check_out_date):
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            r.room_number,
            r.room_name,
            r.category,
            r.price_per_night,
            r.max_capacity
        FROM rooms r
        WHERE r.is_active = 1
        AND NOT EXISTS (
            SELECT 1
            FROM bookings b
            WHERE b.room_id = r.room_id
            AND b.status IN ('Подтверждено', 'Активно')
            AND (
                (b.check_in_date <= ? AND b.check_out_date >= ?)
                OR (b.check_in_date <= ? AND b.check_out_date >= ?)
                OR (b.check_in_date >= ? AND b.check_out_date <= ?)
            )
        )
    ''', (check_out_date, check_in_date, check_out_date, check_in_date, check_in_date, check_out_date))
    rooms = cursor.fetchall()
    conn.close()
    return rooms

def create_booking(guest_id, room_id, check_in_date, check_out_date, total_price):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO bookings (guest_id, room_id, check_in_date, check_out_date, total_price, status, source)
            VALUES (?, ?, ?, ?, ?, 'Подтверждено', 'Telegram Bot')
        ''', (guest_id, room_id, check_in_date, check_out_date, total_price))
        conn.commit()
        booking_id = cursor.lastrowid
        conn.close()
        return booking_id
    except Exception as e:
        print(f"❌ Ошибка создания бронирования: {e}")
        conn.close()
        return None

def get_user_bookings(telegram_id):
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            b.booking_id,
            r.room_number,
            r.room_name,
            b.check_in_date,
            b.check_out_date,
            b.total_price,
            b.status,
            b.created_at
        FROM bookings b
        JOIN rooms r ON b.room_id = r.room_id
        JOIN guests g ON b.guest_id = g.guest_id
        WHERE g.telegram_id = ?
        ORDER BY b.created_at DESC
    ''', (telegram_id,))
    bookings = cursor.fetchall()
    conn.close()
    return bookings

def test_connection():
    """Проверяет подключение к БД"""
    conn = get_connection()
    if conn:
        print("✅ Подключение к SQLite установлено!")
        conn.close()
        return True
    else:
        print("❌ НЕ УДАЛОСЬ подключиться к SQLite!")
        return False
