import win32com.client
import sys

# ★★★ НАСТРОЙКИ ДЛЯ 1С 8.5 ★★★
PATH_TO_1C = r"C:\Users\Школа\Documents\InfoBase1"  # Путь к твоей базе
USER_1C = "Администратор"                            # Пользователь
PASSWORD_1C = ""                                     # Пароль

# ★★★ ДЛЯ 1С 8.5 используем V85.COMConnector ★★★
COM_CONNECTOR = "V85.COMConnector"

def connect_to_1c():
    """Подключается к 1С через COM (версия 8.5)"""
    try:
        print("⏳ Подключение к 1С...")
        com = win32com.client.Dispatch(COM_CONNECTOR)
        connection_string = f"File='{PATH_TO_1C}';Usr='{USER_1C}';Pwd='{PASSWORD_1C}'"
        v8 = com.Connect(connection_string)
        print("✅ Подключение к 1С установлено!")
        return v8
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None

def create_booking(v8, booking_data):
    """Создаёт документ бронирования в 1С"""
    try:
        # ★★★ 1. НАХОДИМ ИЛИ СОЗДАЁМ ГОСТЯ ★★★
        guest_ref = find_or_create_guest(v8, booking_data)
        if not guest_ref:
            return False
        
        # ★★★ 2. НАХОДИМ ИЛИ СОЗДАЁМ НОМЕР ★★★
        room_ref = find_or_create_room(v8, booking_data)
        if not room_ref:
            return False
        
        # ★★★ 3. СОЗДАЁМ ДОКУМЕНТ БРОНИРОВАНИЯ ★★★
        docs = v8.Документы.Бронирование
        doc = docs.СоздатьДокумент()
        
        doc.Дата = v8.ТекущаяДата()
        doc.Гость = guest_ref
        doc.НомерКомнаты = room_ref
        doc.ДатаЗаезда = v8.Дата(booking_data['check_in'])
        doc.ДатаВыезда = v8.Дата(booking_data['check_out'])
        doc.ОбщаяСтоимость = booking_data['total_price']
        
        # В 1С 8.5 статус может быть по-другому
        try:
            doc.Статус = v8.Перечисления.СтатусыБронирования.Подтверждено
        except:
            doc.Статус = 1  # или используй текст
        
        doc.Комментарий = f"Из Telegram бота, ID: {booking_data.get('booking_id', '')}"
        doc.Источник = "Telegram Bot"
        
        doc.Записать()
        
        print(f"✅ Бронирование создано! Номер: {doc.Номер}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания бронирования: {e}")
        return False

def find_or_create_guest(v8, booking_data):
    """Находит гостя по телефону или создаёт нового"""
    try:
        # Ищем гостя
        query = v8.НовыйЗапрос()
        query.Текст = f"""
        ВЫБРАТЬ
            Гости.Ссылка КАК Ссылка
        ИЗ
            Справочник.Гости КАК Гости
        ГДЕ
            Гости.Телефон = '{booking_data['phone']}'
        """
        result = query.Выполнить()
        selection = result.Выбрать()
        
        if selection.Следующий():
            return selection.Ссылка
        
        # Если не нашли — создаём нового
        guests = v8.Справочники.Гости
        guest = guests.СоздатьЭлемент()
        guest.Наименование = booking_data['guest_name']
        guest.Телефон = booking_data['phone']
        guest.TelegramID = booking_data.get('telegram_id', 0)
        guest.Записать()
        
        print(f"✅ Создан новый гость: {booking_data['guest_name']}")
        return guest.Ссылка
        
    except Exception as e:
        print(f"❌ Ошибка поиска/создания гостя: {e}")
        return None

def find_or_create_room(v8, booking_data):
    """Находит номер по коду или создаёт новый"""
    try:
        # Ищем номер
        query = v8.НовыйЗапрос()
        query.Текст = f"""
        ВЫБРАТЬ
            Номера.Ссылка КАК Ссылка
        ИЗ
            Справочник.Номера КАК Номера
        ГДЕ
            Номера.Код = '{booking_data['room_number']}'
        """
        result = query.Выполнить()
        selection = result.Выбрать()
        
        if selection.Следующий():
            return selection.Ссылка
        
        # Если не нашли — создаём новый
        rooms = v8.Справочники.Номера
        room = rooms.СоздатьЭлемент()
        room.Код = booking_data['room_number']
        room.Наименование = booking_data.get('room_name', 'Номер ' + booking_data['room_number'])
        room.ЦенаЗаНочь = booking_data.get('price_per_night', 0)
        room.Записать()
        
        print(f"✅ Создан новый номер: {booking_data['room_number']}")
        return room.Ссылка
        
    except Exception as e:
        print(f"❌ Ошибка поиска/создания номера: {e}")
        return None

# =============================================
# ТЕСТОВЫЕ ДАННЫЕ
# =============================================

if __name__ == "__main__":
    print("========================================")
    print("🤖 ПОДКЛЮЧЕНИЕ К 1С 8.5 ЧЕРЕЗ COM")
    print("========================================")
    
    # Подключаемся к 1С
    v8 = connect_to_1c()
    if not v8:
        input("Нажмите Enter для выхода...")
        sys.exit()
    
    # ★★★ ТЕСТОВОЕ БРОНИРОВАНИЕ ★★★
    test_booking = {
        'booking_id': 999,
        'guest_name': 'Тестовый Гость',
        'phone': '+79001234567',
        'telegram_id': 123456789,
        'room_number': '101',
        'room_name': 'Одноместный эконом',
        'price_per_night': 2500,
        'check_in': '20.06.2026',
        'check_out': '25.06.2026',
        'total_price': 12500
    }
    
    print("⏳ Создание бронирования...")
    success = create_booking(v8, test_booking)
    
    if success:
        print("🎉 УСПЕШНО! Бронирование создано в 1С!")
    else:
        print("❌ ОШИБКА при создании бронирования!")
    
    input("\nНажмите Enter для выхода...")
