import os
import datetime
from datetime import timedelta

# Путь к твоим отчетам[cite: 1]
NET_PATH = r"\\your dir"
RAW_DIR = os.path.join(NET_PATH, "raw_reports")


def get_prev_month_label():
    """Вычисляет строку Год_Месяц для предыдущего месяца."""
    now = datetime.datetime.now()
    # Переходим на первое число текущего месяца и делаем шаг назад на 1 день
    prev_month_date = now.replace(day=1) - timedelta(days=1)
    # %Y - год, %B - полное название месяца (на английском)
    return prev_month_date.strftime("%Y_%B")


def check_results():
    print(f"🧐 Проверка результатов в: {NET_PATH}")

    # Получаем метку прошлого месяца (например, '2026_April')
    target_label = get_prev_month_label()
    print(f"🔍 Ищем данные за прошлый период: {target_label}")

    # 1. Проверяем наличие файла в raw_reports
    if os.path.exists(RAW_DIR):
        # Ищем файлы, в названии которых есть год и название месяца
        files = [f for f in os.listdir(RAW_DIR) if target_label in f]
        if files:
            print(f"✅ Найдены данные за прошлый месяц: {files}")
        else:
            print(f"⚠️ В raw_reports нет файлов за месяц {target_label}")
    else:
        print(f"❌ ОШИБКА: Папка {RAW_DIR} недоступна.")

    # 2. Проверяем отчет KZT
    kzt_dir = os.path.join(NET_PATH, "1")
    if os.path.exists(kzt_dir):
        month_files = [f for f in os.listdir(kzt_dir) if target_label in f]
        if month_files:
            print(f"✅ Отчет [1] успешно создан: {month_files}")
        else:
            print(f"⚠️ [1] В папке  {kzt_dir} отчет за {target_label} не найден.")
    else:
        print(f"? [1] Папка не найдена: {kzt_dir} ")

    # 3. Проверяем отчет WRONG
    wrong_dir = os.path.join(NET_PATH, "2")
    if os.path.exists(wrong_dir):
        month_files = [f for f in os.listdir(wrong_dir) if target_label in f]
        if month_files:
            print(f"✅ Отчет [2] успешно создан: {month_files}")
        else:
            print(f"⚠️ [2] В папке  {wrong_dir} отчет за {target_label} не найден.")
    else:
        print(f"? [2] Папка не найдена: {wrong_dir} ")


if __name__ == "__main__":
    check_results()
