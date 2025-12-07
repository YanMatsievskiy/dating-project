# dating_app/management/commands/load_mock_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dating_app.models import UserProfile, Interest
import random
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Загружает моковые данные в базу данных'

    def handle(self, *args, **options):
        # Создаем увлечения
        interests_list = ["Игры", "Книги", "Фильмы", "Музыка", "Спорт", "Путешествия", "Кулинария", "Искусство"]
        interests = []
        for name in interests_list:
            interest, created = Interest.objects.get_or_create(name=name)
            interests.append(interest)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создано увлечение: {name}'))

        # Города
        cities = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону"]

        # Статусы
        statuses = ["searching", "taken", "complicated"]

        # Пол
        genders = ["M", "F"]

        # Генерируем пользователей
        for i in range(1000): # Создаем 1000 пользователей
            username = f"user{i:04d}" # user0000, user0001, ...
            email = f"{username}@example.com"
            password = "defaultpass123" # Установите стандартный пароль

            user = User.objects.create_user(username=username, email=email, password=password)
            profile = UserProfile.objects.create(
                user=user,
                first_name=f"Имя{i}",
                last_name=f"Фамилия{i}",
                gender=random.choice(genders),
                birth_date=date.today() - timedelta(days=random.randint(365 * 18, 365 * 60)), # Возраст от 18 до 60
                city=random.choice(cities),
                status=random.choice(statuses),
                privacy_setting='public' # Сделаем их публичными для тестирования
            )

            # Добавим случайные увлечения
            selected_interests = random.sample(interests, k=random.randint(1, 3)) # От 1 до 3 увлечений
            profile.interests.set(selected_interests)

            self.stdout.write(self.style.SUCCESS(f'Создан пользователь: {username}'))

        self.stdout.write(self.style.SUCCESS('Загрузка моковых данных завершена!'))