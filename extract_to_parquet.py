import oracledb
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Загружаем настройки
load_dotenv()

# Принудительный Thin Mode
oracledb.init_oracle_client = None

# Читаем строку и превращаем её в список, убирая лишние пробелы
target_teh_input = os.getenv("TARGET_TEH", "").replace('"', '').replace("'", "")
TARGET_TEH_LIST = [item.strip() for item in target_teh_input.split(",") if item.strip()]

def get_connection():
    dsn_tns = f"""(DESCRIPTION=
                    (ADDRESS=(PROTOCOL=TCP)(HOST={os.getenv('DB_HOST')})(PORT={os.getenv('DB_PORT', '1521')}))
                    (CONNECT_DATA=(SERVICE_NAME={os.getenv('DB_SERVICE')}))
                  )"""
    return oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dsn=dsn_tns
    )


def get_week_range():
    now = datetime.now()
    this_week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    start_dt = this_week_start - timedelta(days=7)
    end_dt = this_week_start - timedelta(seconds=1)
    return start_dt, end_dt


def extract_weekly_data():
    start_dt, end_dt = get_week_range()
    s_date = start_dt.strftime('%Y-%m-%d %H:%M:%S')
    e_date = end_dt.strftime('%Y-%m-%d %H:%M:%S')

    # Формируем строки дат для названия файла (20260316_20260322)
    file_period = f"{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"

    print(f"Выгрузка за период: {s_date} - {e_date}...")

    # Используем LISTAGG с ON OVERFLOW TRUNCATE, чтобы избежать ошибок длинных строк
    # И REGEXP_REPLACE для удаления непечатаемых символов
    query = f"""
SELECT /here your script
    """

    conn = None
    try:
        print(f"Выгрузка за период: {s_date} - {e_date}...")
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)

        if not df.empty:
            # Конвертируем все LOB-объекты (сообщения) в обычный текст
            df['MESSAGE'] = df['MESSAGE'].apply(lambda x: x.read() if hasattr(x, 'read') else str(x))

            # Убираем лишние XML-символы, если они проскочат (спец-символы &quot; и т.д.)
            df['MESSAGE'] = df['MESSAGE'].str.replace('&quot;', '"').str.replace('&amp;', '&')

        # Если в колонке MESSAGE пришел LOB-объект, читаем его содержимое как строку
        if 'MESSAGE' in df.columns:
            df['MESSAGE'] = df['MESSAGE'].apply(lambda x: x.read() if hasattr(x, 'read') else str(x))

        # --- ПРОДОЛЖЕНИЕ КОДА ---
        df['TEH'] = df['TEH'].astype(str).str.strip()
        # ... (далее сохранение в parquet)

        # Очистка TEH (убираем лишние пробелы)
        df['TEH'] = df['TEH'].astype(str).str.strip()

        # Формируем прямую ссылку на тикет
        df['LINK'] = 'http://sao.kcell.kz/bt/view?id=' + df['ID_TICKET'].astype(str)

        # Выбираем итоговый набор столбцов для Parquet
        final_cols = [
            'LINK', 'etc'
        ]
        df = df[final_cols]

        # --- СОХРАНЕНИЕ ---
        raw_dir = os.getenv("RAW_DATA_PATH", "./raw_week_reports/")
        if not os.path.exists(raw_dir):
            os.makedirs(raw_dir)

        start_dt, end_dt = get_last_week_range()
        week_str = start_dt.strftime('%G_W%V')
        filename = f"raw_week_{week_str}.parquet"

        # 4. Сборка полного пути
        file_path = os.path.join(raw_dir, filename)

        # 5. Сохранение данных
        try:
            df.to_parquet(file_path, index=False, engine='pyarrow', compression='snappy')
            print(f"✅ Файл успешно сохранен: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")
            return None
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    extract_weekly_data()
