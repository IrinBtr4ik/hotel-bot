import telebot
import pymssql
import os
from datetime import datetime

# =============================================
# НАСТРОЙКИ
# =============================================

# Telegram токен
TOKEN = "8884031821:AAFoIkaqm6lsjKRzhaA0cCPRo8XquU6-aLc"

# ★★★ ПОДКЛЮЧЕНИЕ К MS SQL ★★★
DB_CONFIG = {
    'server': 'localhost',           # или '127.0.0.1'
    'user': 'sa',                    # логин SQL Server
    'password': 'YourStrongPassword', # пароль
    'database': 'HotelBotDB'
}

# =============================================
# ПОДКЛЮЧЕНИЕ К БД
# =============================================

def get_db_connection():
    """Создает подключение к MS SQL"""
    try:
        conn = pymssql.connect(
            server=DB_CONFIG['server'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return None

def get_room_by_number(room_number):
    """Получить информацию о номере по его номеру"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT RoomID, RoomNumber, RoomName, Category, PricePerNight, MaxCapacity
            FROM Rooms
            WHERE RoomNumber = %s AND IsActive = 1
        """, (room_number,))
        room = cursor.fetchone()
        return room
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return None
    finally:
        conn.close()

def get_guest_by_telegram_id(telegram_id):
    """Найти гостя по Telegram ID"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT GuestID, TelegramID, FullName, Phone FROM Guests WHERE TelegramID = %s", (telegram_id,))
        guest = cursor.fetchone()
        return guest
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return None
    finally:
        conn.close()

def create_guest(telegram_id, full_name, phone):
    """Создать нового гостя"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Guests (TelegramID, FullName, Phone, CreatedAt)
            VALUES (%s, %s, %s, GETDATE())
        """, (telegram_id, full_name, phone))
        conn.commit()
        
        # Получаем ID созданного гостя
        cursor.execute("SELECT SCOPE_IDENTITY() AS GuestID")
        guest_id = cursor.fetchone()[0]
        return guest_id
    except Exception as e:
        print(f"❌ Ошибка создания гостя: {e}")
        return None
    finally:
        conn.close()

def create_booking(guest_id, room_id, check_in, check_out, total_price):
    """Создать бронирование"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Bookings (GuestID, RoomID, CheckInDate, CheckOutDate, TotalPrice, Status, Source, CreatedAt)
            VALUES (%s, %s, %s, %s, %s, 'Подтверждено', 'Telegram Bot', GETDATE())
        """, (guest_id, room_id, check_in, check_out, total_price))
        conn.commit()
        
        cursor.execute("SELECT SCOPE_IDENTITY() AS BookingID")
        booking_id = cursor.fetchone()[0]
        return booking_id
    except Exception as e:
        print(f"❌ Ошибка создания бронирования: {e}")
        return None
    finally:
        conn.close()

def get_user_bookings(telegram_id):
    """Получить все бронирования пользователя"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
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
        """, (telegram_id,))
        bookings = cursor.fetchall()
        return bookings
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return []
    finally:
        conn.close()

def search_free_rooms(check_in, check_out):
    """Поиск свободных номеров на даты"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
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
        """, (check_out, check_in, check_out, check_in, check_in, check_out))
        
        rooms = cursor.fetchall()
        return rooms
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return []
    finally:
        conn.close()

# =============================================
# ТЕЛЕГРАМ БОТ
# =============================================

bot = telebot.TeleBot(TOKEN)

# Временное хранилище для состояний диалога
user_data = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    name = message.from_user.first_name
    
    reply = f"🏨 Добро пожаловать, {name}!\n\n" \
            "Доступные команды:\n" \
            "🔍 /search - поиск свободных номеров\n" \
            "📋 /mybookings - мои бронирования\n" \
            "❓ /help - помощь\n\n" \
            "Для бронирования:\n" \
            "бронь Номер ДатаЗаезда ДатаВыезда ФИО Телефон\n" \
            "Пример: бронь 101 20.06.2026 25.06.2026 Иванов Иван +79001234567"
    
    bot.send_message(chat_id, reply)

@bot.message_handler(commands=['help'])
def handle_help(message):
    chat_id = message.chat.id
    reply = "❓ Помощь:\n\n" \
            "/start - главное меню\n" \
            "/search - поиск свободных номеров\n" \
            "/mybookings - мои бронирования\n\n" \
            "Формат бронирования:\n" \
            "бронь Номер ДатаЗаезда ДатаВыезда ФИО Телефон\n" \
            "Пример: бронь 101 20.06.2026 25.06.2026 Иванов Иван +79001234567"
    
    bot.send_message(chat_id, reply)

@bot.message_handler(commands=['search'])
def handle_search(message):
    chat_id = message.chat.id
    
    # По умолчанию ищем на сегодня + 3 дня
    from datetime import datetime, timedelta
    check_in = datetime.now().strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    
    rooms = search_free_rooms(check_in, check_out)
    
    if not rooms:
        bot.send_message(chat_id, "😔 Свободных номеров нет на выбранные даты")
        return
    
    reply = "🏠 Свободные номера:\n\n"
    for room in rooms:
        reply += f"🛏 {room['RoomNumber']} - {room['RoomName']}\n"
        reply += f"   Категория: {room['Category']}\n"
        reply += f"   Цена: {room['PricePerNight']} руб/ночь\n"
        reply += f"   Вместимость: {room['MaxCapacity']} чел.\n\n"
    
    reply += "Для бронирования:\nбронь Номер ДатаЗаезда ДатаВыезда ФИО Телефон\n"
    reply += "Пример: бронь 101 20.06.2026 25.06.2026 Иванов Иван +79001234567"
    
    bot.send_message(chat_id, reply)

@bot.message_handler(commands=['mybookings'])
def handle_mybookings(message):
    chat_id = message.chat.id
    telegram_id = message.from_user.id
    
    bookings = get_user_bookings(telegram_id)
    
    if not bookings:
        bot.send_message(chat_id, "📋 У вас нет активных бронирований.")
        return
    
    reply = "📋 Ваши бронирования:\n\n"
    for booking in bookings:
        reply += f"🔹 Бронь #{booking['BookingID']}\n"
        reply += f"   Номер: {booking['RoomNumber']} - {booking['RoomName']}\n"
        reply += f"   Заезд: {booking['CheckInDate'].strftime('%d.%m.%Y')}\n"
        reply += f"   Выезд: {booking['CheckOutDate'].strftime('%d.%m.%Y')}\n"
        reply += f"   Стоимость: {booking['TotalPrice']} руб.\n"
        reply += f"   Статус: {booking['Status']}\n\n"
    
    bot.send_message(chat_id, reply)

@bot.message_handler(func=lambda message: message.text.startswith('бронь') or message.text.startswith('/book'))
def handle_booking(message):
    chat_id = message.chat.id
    text = message.text
    telegram_id = message.from_user.id
    
    try:
        parts = text.split()
        start_index = 1 if parts[0] in ['бронь', '/book'] else 0
        
        if len(parts) < start_index + 5:
            bot.send_message(chat_id, "❌ Неверный формат!\n\n"
                             "бронь Номер ДатаЗаезда ДатаВыезда ФИО Телефон\n"
                             "Пример: бронь 101 20.06.2026 25.06.2026 Иванов Иван +79001234567")
            return
        
        room_number = parts[start_index]
        check_in = parts[start_index + 1]
        check_out = parts[start_index + 2]
        full_name = parts[start_index + 3]
        phone = parts[start_index + 4]
        
        # Проверяем формат дат
        try:
            check_in_date = datetime.strptime(check_in, "%d.%m.%Y")
            check_out_date = datetime.strptime(check_out, "%d.%m.%Y")
        except ValueError:
            bot.send_message(chat_id, "❌ Неверный формат даты! Используйте ДД.ММ.ГГГГ")
            return
        
        if check_out_date <= check_in_date:
            bot.send_message(chat_id, "❌ Дата выезда должна быть позже даты заезда!")
            return
        
        # Проверяем, существует ли номер
        room = get_room_by_number(room_number)
        if not room:
            bot.send_message(chat_id, f"❌ Номер {room_number} не найден!")
            return
        
        # Находим или создаем гостя
        guest = get_guest_by_telegram_id(telegram_id)
        if not guest:
            guest_id = create_guest(telegram_id, full_name, phone)
            if not guest_id:
                bot.send_message(chat_id, "❌ Ошибка создания гостя!")
                return
        else:
            guest_id = guest['GuestID']
        
        # Рассчитываем стоимость
        days = (check_out_date - check_in_date).days
        total_price = room['PricePerNight'] * days
        
        # Создаем бронирование
        booking_id = create_booking(
            guest_id,
            room['RoomID'],
            check_in_date.strftime("%Y-%m-%d"),
            check_out_date.strftime("%Y-%m-%d"),
            total_price
        )
        
        if booking_id:
            reply = f"✅ Бронирование подтверждено!\n\n" \
                    f"📋 Номер брони: #{booking_id}\n" \
                    f"🏨 Номер: {room['RoomNumber']} - {room['RoomName']}\n" \
                    f"👤 Гость: {full_name}\n" \
                    f"📅 Заезд: {check_in}\n" \
                    f"📅 Выезд: {check_out}\n" \
                    f"💰 Стоимость: {total_price} руб."
            bot.send_message(chat_id, reply)
        else:
            bot.send_message(chat_id, "❌ Ошибка создания бронирования!")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")
        print(f"Ошибка: {e}")

@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "❌ Неизвестная команда. Напишите /help для справки.")

# =============================================
# ЗАПУСК БОТА
# =============================================

if __name__ == "__main__":
    print("========================================")
    print("🤖 TELEGRAM БОТ + MS SQL")
    print("========================================")
    print("✅ БОТ ЗАПУЩЕН!")
    print("📡 Ожидание сообщений...")
    print("========================================")
    
    # Проверяем подключение к БД
    conn = get_db_connection()
    if conn:
        print("✅ Подключение к MS SQL установлено!")
        conn.close()
    else:
        print("❌ Подключение к MS SQL НЕ РАБОТАЕТ!")
    
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
