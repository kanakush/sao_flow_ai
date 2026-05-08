import os
import requests
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()


class TelegramNotifier:
    def __init__(self):
        # Читаем токены из системного окружения
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        # Проверка: загрузились ли данные
        if not self.token or not self.chat_id:
            print("⚠️ Ошибка: TELEGRAM_TOKEN или TELEGRAM_CHAT_ID не найдены в .env")

    def notify(self, message):
        if not self.token: return False

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка Telegram: {e}")
            return False
