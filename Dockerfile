# Dockerfile

FROM python:3.11-slim

# Установка зависимостей для сборки и psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Установка переменной окружения для Django
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# EXPOSE порта (Docker Compose указывает порт)
# EXPOSE 8000

# Команда для запуска (после миграций)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]