import subprocess
import datetime
import sys
import os
from notifier import TelegramNotifier

# 1. ГЛАВНЫЕ НАСТРОЙКИ
# Путь, где лежат сами скрипты (папка, в которой находится этот pipeline.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Сетевой путь для отчетов, который ты указал
RAW_REPORTS_DIR = r'\\your dir'

bot = TelegramNotifier()


def run_task(script_name):
    """Находит скрипт в папке проекта и запускает его."""
    script_path = os.path.join(BASE_DIR, script_name)

    print(f"\n{'=' * 20}")
    print(f"🚀 ЗАПУСК: {script_name}")
    print(f"📍 ПУТЬ: {script_path}")
    print(f"{'=' * 20}")

    if not os.path.exists(script_path):
        error_msg = f"❌ ОШИБКА: Файл {script_name} не найден в папке {BASE_DIR}"
        print(error_msg)
        bot.notify(error_msg)
        return False

    try:
        # Запуск через текущий интерпретатор Python
        subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ ОШИБКА при выполнении {script_name}: Код {e.returncode}"
        print(error_msg)
        bot.notify(error_msg)
        return False


def main():
    now = datetime.datetime.now()
    date_str = now.strftime("%Y:%m:%d")
    time_str = now.strftime("%H:%M:%S")

    bot.notify(f" *Start Pipeline*\n📅Date:{date_str}\n🕒Time:{time_str}")

    # 2. ПОСЛЕДОВАТЕЛЬНОСТЬ ЗАПУСКА
    # Сначала всегда выгрузка данных
    if not run_task("extract_to_parquet.py"):
        print("⛔ Критическая ошибка выгрузки. Pipline остановлен.")
        return

    # Список аналитических скриптов
    analytics_scripts = ["omni_ai.py", "superapp_ai.py"]

    for script in analytics_scripts:
        run_task(script)

    # 3. ЕЖЕМЕСЯЧНЫЕ ЗАДАЧИ (только 1-го числа)
    if date_str == 1:
        print("\n📅 Первое число месяца! Запуск спец. отчетов...")
        run_task("extract_monthly_wrong.py", )
        run_task("wrong.py")
    else:
        print(f"\nℹ️ Сегодня {date_str}-е число. Пропуск ежемесячных задач.")

    # 4. ФИНАЛЬНЫЙ ЭТАП
    run_task("post_processing.py")

    duration = datetime.datetime.now() - now
    finish_msg = f" *Pipline завершен*\n Время выполнения: {duration}"
    print(f"\n{finish_msg}")
    bot.notify(finish_msg)


if __name__ == "__main__":
    main()
