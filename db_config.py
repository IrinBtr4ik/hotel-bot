DB_CONFIG = {
    'server': 'localhost',           # Имя сервера (или IP)
    'port': 1433,                    # Порт (по умолчанию 1433)
    'user': 'LENOVO-1041623\SQLEXPRESS',                    # Логин SQL Server
    'password': '', # Пароль
    'database': 'HotelDB'         # Имя базы данных
}

# Альтернативная строка подключения для pyodbc
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=HotelDB;"
    "UID=LENOVO-1041623\SQLEXPRESS;"
    "PWD="
)
