
# main.py - Telegram бот для бронирования отелей
# База данных: SQLite


import telebot
from datetime import datetime, timedelta
from db import (
    test_connection,
    create_tables,
    init_rooms,
    get_guest_by_telegram_id,
    create_guest,
    get_room_by_number,
    get_all_rooms,
    search_free_rooms,
    create_booking,
    get_user_bookings
)

# токен
TOKEN = "8884031821:AAFoIkaqm6lsjKRzhaA0cCPRo8XquU6-aLc"  # ← ЗАМЕНИ НА СВОЙ!

# создание бота
bot = telebot.TeleBot(TOKEN)

# =============================================
# ОБРАБОТЧИКИ КОМАНД
# =============================================

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
    
    # По умолчанию — сегодня и +3 дня
    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    
    rooms = search_free_rooms(today, future)
    
    if not rooms:
        bot.send_message(chat_id, "😔 На выбранные даты свободных номеров нет.")
        return
    
    reply = "🏠 Свободные номера:\n\n"
    for room in rooms:
        reply += f"🛏 {room['room_number']} - {room['room_name']}\n"
        reply += f"   Категория: {room['category']}\n"
        reply += f"   Цена: {room['price_per_night']} руб/ночь\n"
        reply += f"   Вместимость: {room['max_capacity']} чел.\n\n"
    
    reply += "Для бронирования:\n"
    reply += "бронь Номер ДатаЗаезда ДатаВыезда ФИО Телефон\n"
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
        reply += f"🔹 Бронь #{booking['booking_id']}\n"
        reply += f"   Номер: {booking['room_number']} - {booking['room_name']}\n"
        reply += f"   Заезд: {booking['check_in_date']}\n"
        reply += f"   Выезд: {booking['check_out_date']}\n"
        reply += f"   Стоимость: {booking['total_price']} руб.\n"
        reply += f"   Статус: {booking['status']}\n\n"
    
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
        
        # проверка дат
        try:
            check_in_date = datetime.strptime(check_in, "%d.%m.%Y")
            check_out_date = datetime.strptime(check_out, "%d.%m.%Y")
        except ValueError:
            bot.send_message(chat_id, "❌ Неверный формат даты! Используйте ДД.ММ.ГГГГ")
            return
        
        if check_out_date <= check_in_date:
            bot.send_message(chat_id, "❌ Дата выезда должна быть позже даты заезда!")
            return
        
        # проверка номера
        room = get_room_by_number(room_number)
        if not room:
            bot.send_message(chat_id, f"❌ Номер {room_number} не найден!")
            return
        
        # поиск или создание гостя
        guest = get_guest_by_telegram_id(telegram_id)
        if not guest:
            guest_id = create_guest(telegram_id, full_name, phone)
            if not guest_id:
                bot.send_message(chat_id, "❌ Ошибка создания гостя!")
                return
        else:
            guest_id = guest['guest_id']
        
        # расчет стоимости
        days = (check_out_date - check_in_date).days
        total_price = room['price_per_night'] * days
        
        # создание бронирования
        booking_id = create_booking(
            guest_id,
            room['room_id'],
            check_in_date.strftime("%Y-%m-%d"),
            check_out_date.strftime("%Y-%m-%d"),
            total_price
        )
        
        if booking_id:
            reply = f"✅ Бронирование подтверждено!\n\n" \
                    f"📋 Номер брони: #{booking_id}\n" \
                    f"🏨 Номер: {room['room_number']} - {room['room_name']}\n" \
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


# ЗАПУС

if __name__ == "__main__":
    print("========================================")
    print("🤖 TELEGRAM БОТ + SQLite")
    print("========================================")
    
    # инициализация баз данных
    create_tables()
    init_rooms()
    
    if test_connection():
        print("✅ БОТ ЗАПУЩЕН!")
        print("📡 Ожидание сообщений...")
        print("========================================")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    else:
        print("❌ БОТ НЕ ЗАПУЩЕН — проверьте настройки БД!")
