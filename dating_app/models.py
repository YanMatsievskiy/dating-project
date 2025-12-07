# dating_app/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
import os

class User(AbstractUser):
    """
    Кастомная модель пользователя.
    """
    email = models.EmailField(unique=True) # Уникальный email

    USERNAME_FIELD = 'email' # Используем email для входа
    REQUIRED_FIELDS = ['username'] # Обязательные поля при создании суперпользователя

    def __str__(self):
        return self.username


class Interest(models.Model):
    """
    Модель для увлечений.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Название увлечения")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Увлечение"
        verbose_name_plural = "Увлечения"


def user_profile_photo_path(instance, filename):
    """
    Генерирует путь для загрузки фото профиля.
    """
    # Файлы будут загружаться в MEDIA_ROOT/profile_photos/user_<id>/<filename>
    return os.path.join('profile_photos', f'user_{instance.user.id}', filename)

class UserProfile(models.Model):
    """
    Модель профиля пользователя.
    """
    STATUS_CHOICES = [
        ('searching', 'В поиске'),
        ('taken', 'Занят(а)'),
        ('complicated', 'Всё сложно'),
    ]

    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
        ('O', 'Другое'),
    ]

    PRIVACY_CHOICES = [
        ('public', 'Публичный'),
        ('private', 'Приватный'),
        ('friends', 'Только для друзей'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=100, blank=True, null=True, verbose_name="Отчество")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Пол")
    birth_date = models.DateField(verbose_name="Дата рождения")
    city = models.CharField(max_length=100, verbose_name="Город")
    interests = models.ManyToManyField(Interest, blank=True, verbose_name="Увлечения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='searching', verbose_name="Статус")
    photo_gallery = models.ImageField(upload_to=user_profile_photo_path, blank=True, null=True, verbose_name="Фото профиля")
    main_photo = models.ImageField(upload_to=user_profile_photo_path, blank=True, null=True, verbose_name="Заглавное фото")
    likes_count = models.PositiveIntegerField(default=0, verbose_name="Количество лайков")
    privacy_setting = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public', verbose_name="Настройка приватности")

    def get_age(self):
        """
        Вычисляет возраст пользователя.
        """
        from datetime import date
        today = date.today()
        age = today.year - self.birth_date.year
        if today.month < self.birth_date.month or (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        return age

    def get_full_name(self):
        """
        Возвращает полное имя пользователя.
        """
        full_name_parts = [self.first_name, self.patronymic, self.last_name]
        return " ".join(part for part in full_name_parts if part)

    def __str__(self):
        return f"Профиль {self.get_full_name()} ({self.user.username})"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
        ordering = ['user__username']


def delete_profile_photo(sender, instance, **kwargs):
    """
    Удаляет файл фото с диска при удалении объекта UserProfile.
    """
    if instance.photo_gallery:
        if os.path.isfile(instance.photo_gallery.path):
            os.remove(instance.photo_gallery.path)
    if instance.main_photo:
        if os.path.isfile(instance.main_photo.path):
            os.remove(instance.main_photo.path)

# Подключаем сигнал к модели UserProfile
models.signals.post_delete.connect(delete_profile_photo, sender=UserProfile)

# --- Модель для лайков/дизлайков (K2) ---
class LikeDislike(models.Model):
    """
    Модель для хранения лайков и дизлайков.
    """
    LIKE = 1
    DISLIKE = -1

    VOTE_CHOICES = [
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    ]

    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes_given', verbose_name="Голосующий")
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes_received', verbose_name="Цель голосования")
    vote = models.SmallIntegerField(choices=VOTE_CHOICES, verbose_name="Голос (лайк/дизлайк)")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    class Meta:
        unique_together = ('voter', 'target_user') # Один пользователь может проголосовать за другого только один раз
        verbose_name = "Голос (лайк/дизлайк)"
        verbose_name_plural = "Голоса (лайки/дизлайки)"

# --- Модель истории просмотров (K3.1) ---
class ViewHistory(models.Model):
    """
    Модель для хранения истории просмотров профилей.
    """
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles_viewed', verbose_name="Просматривающий")
    viewed_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Просмотренный профиль")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время просмотра")

    class Meta:
        verbose_name = "Просмотр профиля"
        verbose_name_plural = "Просмотры профилей"
        # Уникальность не требуется, пользователь может смотреть один профиль несколько раз
        # unique_together = ('viewer', 'viewed_profile') # <-- Можно добавить, если нужна уникальность

# --- Модель понравившихся пользователей (K3.2) ---
class LikedUsers(models.Model):
    """
    Модель для хранения списка понравившихся пользователей.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_users_list', verbose_name="Пользователь")
    liked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_by_users', verbose_name="Понравившийся пользователь")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        unique_together = ('user', 'liked_user') # Пользователь не может дважды добавить в понравившиеся
        verbose_name = "Понравившийся пользователь"
        verbose_name_plural = "Понравившиеся пользователи"

# --- Модель непонравившихся пользователей (K3.3) ---
class DislikedUsers(models.Model):
    """
    Модель для хранения списка непонравившихся пользователей.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disliked_users_list', verbose_name="Пользователь")
    disliked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disliked_by_users', verbose_name="Непонравившийся пользователь")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        unique_together = ('user', 'disliked_user') # Пользователь не может дважды добавить в непонравившиеся
        verbose_name = "Непонравившийся пользователь"
        verbose_name_plural = "Непонравившиеся пользователи"

# --- Модель истории лайков (K3.4) ---
class LikeHistory(models.Model):
    """
    Модель для хранения истории лайков пользователя.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given_history', verbose_name="Пользователь")
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received_history', verbose_name="Цель лайка")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата лайка")

    class Meta:
        verbose_name = "История лайка"
        verbose_name_plural = "Истории лайков"

# --- Модель взаимного лайка (матча) и приглашения (K3.5) ---
class Match(models.Model):
    """
    Модель для хранения взаимных лайков (матчей).
    """
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_initiated', verbose_name="Пользователь 1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_received', verbose_name="Пользователь 2")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата матча")

    class Meta:
        unique_together = ('user1', 'user2') # Один матч между двумя пользователями
        verbose_name = "Матч"
        verbose_name_plural = "Матчи"

# --- Модель чата (для доп. задания) ---
class Chat(models.Model):
    """
    Модель для чата между двумя пользователями.
    """
    participants = models.ManyToManyField(User, related_name='chats', verbose_name="Участники чата")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        participant_usernames = [p.username for p in self.participants.all()]
        return f"Чат: {' и '.join(participant_usernames)}"

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"

# --- Модель сообщения (для доп. задания) ---
class Message(models.Model):
    """
    Модель для сообщения в чате.
    """
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages', verbose_name="Чат")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Отправитель")
    content = models.TextField(verbose_name="Содержание сообщения")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")

    def __str__(self):
        return f"Сообщение от {self.sender.username} в {self.chat.id} в {self.timestamp}"

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['timestamp']