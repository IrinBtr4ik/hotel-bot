import telebot
import requests
import json
import os

# ★★★ ТОКЕН ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ★★★
TOKEN = os.getenv("BOT_TOKEN", "8884031821:AAFoIkaqm6lsjKRzhaA0cCPRo8XquU6-aLc")

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

    # ★★★ ЗАГЛУШКА ★★★
    reply = "🏠 Свободные номера (ТЕСТ):\n\n" \
            "🛏 101 - Одноместный эконом (2 500 руб/ночь)\n" \
            "🛏 102 - Двухместный эконом (3 000 руб/ночь)\n" \
            "🛏 201 - Стандарт (4 500 руб/ночь)\n" \
            "🛏 301 - Люкс с джакузи (8 500 руб/ночь)\n\n" \
            "Для бронирования: бронь 101 20.06.2026 25.06.2026 Иванов Иван +79001234567"

    bot.send_message(chat_id, reply)


@bot.message_handler(commands=['mybookings'])
def handle_mybookings(message):
    chat_id = message.chat.id

    reply = "📋 Ваши бронирования:\n\n" \
            "🔹 Бронь #0001\n" \
            "   Номер: 101\n" \
            "   Заезд: 20.06.2026\n" \
            "   Выезд: 25.06.2026\n" \
            "   Стоимость: 12 500 руб.\n" \
            "   Статус: Подтверждено\n\n" \
            "🔹 Бронь #0002\n" \
            "   Номер: 201\n" \
            "   Заезд: 05.07.2026\n" \
            "   Выезд: 10.07.2026\n" \
            "   Стоимость: 22 500 руб.\n" \
            "   Статус: Активно"

    bot.send_message(chat_id, reply)


@bot.message_handler(func=lambda message: message.text.startswith('бронь') or message.text.startswith('/book'))
def handle_booking(message):
    chat_id = message.chat.id
    text = message.text

    try:
        parts = text.split()
        start_index = 1 if parts[0] in ['бронь', '/book'] else 0

        if len(parts) < start_index + 5:
            bot.send_message(chat_id, "❌ Неверный формат!\n\n"
                             "бронь Номер ДатаЗаезда ДатаВыезда ФИО Телефон\n"
                             "Пример: бронь 101 20.06.2026 25.06.2026 Иванов Иван +79001234567")
            return

        number = parts[start_index]
        check_in = parts[start_index + 1]
        check_out = parts[start_index + 2]
        full_name = parts[start_index + 3]
        phone = parts[start_index + 4]

        reply = f"✅ Бронирование подтверждено!\n\n" \
                f"📋 Номер: {number}\n" \
                f"👤 Гость: {full_name}\n" \
                f"📅 Заезд: {check_in}\n" \
                f"📅 Выезд: {check_out}"

        bot.send_message(chat_id, reply)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")


@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "❌ Неизвестная команда. Напишите /help для справки.")


# =============================================
# ЗАПУСК БОТА
# =============================================

if __name__ == "__main__":
    print("========================================")
    print("🤖 TELEGRAM БОТ НА PYTHON (BOTHOST)")
    print("========================================")
    print("✅ БОТ ЗАПУЩЕН!")
    print("📡 Ожидание сообщений...")
    print("========================================")

    bot.infinity_polling(timeout=60, long_polling_timeout=60)
