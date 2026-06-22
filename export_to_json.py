import sqlite3
import json
import os

# ★★★ ПУТЬ К БАЗЕ ДАННЫХ ★★★
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'database.db')

def export_to_json():
    """Экспортирует данные из SQLite в JSON-файл"""
    
    # Проверяем, существует ли база
    if not os.path.exists(DB_PATH):
        print(f"❌ База не найдена: {DB_PATH}")
        return
    
    # Подключаемся к базе
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # ★★★ 1. ЭКСПОРТ ГОСТЕЙ ★★★
    cursor.execute("SELECT * FROM guests")
    guests = [dict(row) for row in cursor.fetchall()]
    
    # ★★★ 2. ЭКСПОРТ НОМЕРОВ ★★★
    cursor.execute("SELECT * FROM rooms")
    rooms = [dict(row) for row in cursor.fetchall()]
    
    # ★★★ 3. ЭКСПОРТ БРОНИРОВАНИЙ ★★★
    cursor.execute('''
        SELECT 
            b.booking_id,
            g.full_name AS guest_name,
            g.phone,
            g.telegram_id,
            r.room_number,
            r.room_name,
            b.check_in_date,
            b.check_out_date,
            b.total_price,
            b.status,
            b.created_at
        FROM bookings b
        JOIN guests g ON b.guest_id = g.guest_id
        JOIN rooms r ON b.room_id = r.room_id
        ORDER BY b.created_at DESC
    ''')
    bookings = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # ★★★ 4. ФОРМИРУЕМ ИТОГОВЫЙ JSON ★★★
    data = {
        'export_date': str(datetime.now()),
        'guests_count': len(guests),
        'rooms_count': len(rooms),
        'bookings_count': len(bookings),
        'guests': guests,
        'rooms': rooms,
        'bookings': bookings
    }
    
    # ★★★ 5. СОХРАНЯЕМ JSON ★★★
    output_path = '/tmp/1c_export.json'  # для Bothost
    # output_path = 'C:\\1c_export.json'  # для Windows
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ Экспорт завершён!")
    print(f"   📁 Файл: {output_path}")
    print(f"   👤 Гостей: {len(guests)}")
    print(f"   🏨 Номеров: {len(rooms)}")
    print(f"   📋 Бронирований: {len(bookings)}")
    
    return output_path

if __name__ == "__main__":
    from datetime import datetime
    export_to_json()
