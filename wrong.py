import os
import glob
import pandas as pd


# --- УТИЛИТЫ ---
def convert_to_hms(total_hours):
    if pd.isna(total_hours) or total_hours < 0:
        return "00:00:00"
    total_seconds = int(round(total_hours * 3600))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def process_category(df, cat_name, week_label):
    if df is None or df.empty:
        print(f"--- Пропуск {cat_name}: данных нет ---")
        return

    # Указываем сетевой путь с префиксом r перед строкой
    base_dir = r'\\your dir'

    # Формируем полный путь
    out_dir = os.path.join(base_dir, cat_name)

    # Создаем папку, если она не существует
    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, f"Report_{cat_name}_{week_label}.xlsx")

    # Сохранение в Excel
    with pd.ExcelWriter(out_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Анализ', index=False)

    print(f"💾 Успешно сохранено: {out_file}")


def main():
    raw_dir = r'\\your dir'
    files = glob.glob(os.path.join(raw_dir, "raw_month_*.parquet"))
    if not files:
        print("❌ Ошибка: Нет файлов .parquet.")
        return

    input_file = max(files, key=os.path.getctime)
    week_label = os.path.basename(input_file).replace("raw_month_", "").replace(".parquet", "")

    # Читаем файл и удаляем дубликаты
    df_all = pd.read_parquet(input_file).drop_duplicates(subset=['ID_TICKET'])

    contract_pattern = 'Ошибочный запрос'
    df_contract = df_all[df_all['TEH'].fillna('').str.contains(contract_pattern, case=False)].copy()

    # ПРОСТОЙ ВЫЗОВ ФУНКЦИИ (без asyncio)
    if not df_contract.empty:
        process_category(df_contract, "WRONG", week_label)

    print("\n✅ Готово.")


if __name__ == "__main__":
    main()
