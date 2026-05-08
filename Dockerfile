# Используем стабильный легкий образ Python
FROM python:3.10-slim

# Установка системных зависимостей для Oracle DB и работы с сетью
RUN apt-get update && apt-get install -y \
    libaio1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Установка библиотек Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все исходники проекта
COPY . .

# Создаем папку для логов и монтирования отчетов
RUN mkdir -p /app/logs /mnt/reports

# Запуск основного пайплайна при старте контейнера
CMD ["python", "pipeline.py"]