import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST")
print(f"--- DEBUG ---")
print(f"Host: [{os.getenv('DB_HOST')}]")
print(f"Service Name: [{os.getenv('DB_SERVICE')}]")
print(f"DB_PORT: [{os.getenv('DB_PORT')}] ")
print(f"DB_PASS: [{os.getenv('DB_PASS')}] ")
print(f"DB_USER: [{os.getenv('DB_USER')}] ")

# Безопасное получение переменных
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "1521") # 1521 по умолчанию
db_name = os.getenv("DB_SERVICE")

# Формируем TNS строку
dsn_tns = f"""(DESCRIPTION=
                (ADDRESS=(PROTOCOL=TCP)(HOST={db_host})(PORT={db_port}))
                (CONNECT_DATA=(SERVICE_NAME={db_name}))
              )"""

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "dsn": dsn_tns
}

def get_db_connection():
    return oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dsn=dsn_tns,
    )
