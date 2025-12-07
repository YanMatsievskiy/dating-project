Приложение для знакомств (Django/DRF)

1. Описание
Проект представляет собой веб-платформу для знакомств, на Django и Django REST Framework (DRF).
- Пользователи могут регистрироваться и авторизовываться по email.
- Можно создавать и редактировать профиль (ФИО, пол, возраст, город, увлечения, статус, фото, настройки приватности).
- Система лайков/дизлайков для взаимодействия с другими профилями.
- Возможность просмотра случайного профиля с фильтрацией.
- Хранение истории просмотров, списков понравившихся/непонравившихся, истории лайков.
- API документирован с помощью Swagger.
- Проект упакован в Docker-контейнеры и запускается с помощью docker-compose.
- Используется PostgreSQL для хранения данных.

2. Структура файлов
- `manage.py`: Скрипт для управления проектом.
- `myproject/`: Директория основного проекта.
  - `settings.py`: Конфигурация проекта (БД, DRF, JWT, CORS).
  - `urls.py`: Основные URL-адреса.
- `dating_app/`: Приложение для функционала знакомств.
  - `models.py`: Модели `User`, `UserProfile`, `Interest`, `LikeDislike`, `ViewHistory`, `LikedUsers`, `DislikedUsers`, `LikeHistory`, `Match`, `Chat`, `Message`.
  - `serializers.py`: Сериализаторы для моделей.
  - `views.py`: API-представления (ViewSet, APIView, функции лайк/дизлайк, случайный профиль).
  - `permissions.py`: Класс прав доступа `IsOwnerOrReadOnly`.
  - `urls.py`: URL-адреса API.
  - `tests.py`: (или `tests/`) Тесты для системы взаимодействия (K7).
  - `migrations/`: (Генерируются Django).
  - `management/commands/load_mock_data.py`: (Доп. задание) Команда для загрузки моковых данных.
  - `consumers.py`: (Доп. задание) Код для WebSocket.
  - `routing.py`: (Доп. задание) Роутинг для WebSocket.
- `Dockerfile`: Инструкции для сборки образа приложения.
- `docker-compose.yml`: Конфигурация для запуска приложения и PostgreSQL.
- `requirements.txt`: Зависимости проекта.
- `README.md`: Описание проекта.

3. Запуск с помощью Docker Compose
Для запуска проекта необходим Docker и Docker Compose.
Установка Docker и Docker Compose
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

4. Запуск приложения:
4.1.  **Откройте терминал** в папке проекта (где лежит `docker-compose.yml`).
4.2.  **(Опционально) Создайте файл `.env` для настройки переменных окружения:**
    ```bash
    # .env
    POSTGRES_DB=dating_app_db
    POSTGRES_USER=dating_user
    POSTGRES_PASSWORD=dating_pass
    SECRET_KEY=your-very-long-and-random-secret-key-here
    ```
4.3.  **Выполните команду для сборки и запуска:**
    ```bash
    docker-compose up --build
    ```
    Эта команда:
    - Соберет Docker-образ приложения из `Dockerfile`.
    - Запустит сервисы `db` (PostgreSQL) и `web` (Django).
    - Выполнит миграции базы данных.
    - (Если реализована) загрузит моковые данные.
    - Свяжет порт 8000 (Django) с вашим локальным хостом.

5. Просмотр в браузере:
5.1.  Откройте веб-браузер.
5.2.  Перейдите по адресу `http://localhost:8000/api/docs/` для просмотра документации Swagger.
5.3.  API-эндпоинты будут доступны по адресу `http://localhost:8000/api/...`.

6. Дополнительные команды:
- **Создать суперпользователя:**
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```
- **Запустить тесты:**
    ```bash
    docker-compose exec web python manage.py test dating_app
    ```
- **Остановить и удалить контейнеры:**
    ```bash
    docker-compose down
    ```
