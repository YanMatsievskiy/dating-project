# dating_app/tests.py (или dating_app/tests/test_interaction.py)

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserProfile, LikeDislike

User = get_user_model()

class InteractionTestCase(TestCase):
    def setUp(self):
        # Создаем пользователей для тестов
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='testpass123')
        # Создаем профили для пользователей
        self.profile1 = UserProfile.objects.create(
            user=self.user1, first_name='Иван', last_name='Иванов', gender='M',
            birth_date='1990-01-01', city='Москва'
        )
        self.profile2 = UserProfile.objects.create(
            user=self.user2, first_name='Мария', last_name='Петрова', gender='F',
            birth_date='1992-05-15', city='Санкт-Петербург'
        )
        # Создаем API-клиент и авторизуем user1
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    def test_like_user(self):
        """
        Тест: Пользователь может лайкнуть другого пользователя.
        """
        url = reverse('dating_app:like_dislike', kwargs={'user_id': self.user2.id})
        data = {'vote': 1} # Лайк
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LikeDislike.objects.count(), 1)
        vote = LikeDislike.objects.get()
        self.assertEqual(vote.voter, self.user1)
        self.assertEqual(vote.target_user, self.user2)
        self.assertEqual(vote.vote, LikeDislike.LIKE)

    def test_dislike_user(self):
        """
        Тест: Пользователь может дизлайкнуть другого пользователя.
        """
        url = reverse('dating_app:like_dislike', kwargs={'user_id': self.user2.id})
        data = {'vote': -1} # Дизлайк
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LikeDislike.objects.count(), 1)
        vote = LikeDislike.objects.get()
        self.assertEqual(vote.voter, self.user1)
        self.assertEqual(vote.target_user, self.user2)
        self.assertEqual(vote.vote, LikeDislike.DISLIKE)

    def test_mutual_like_creates_match(self):
        """
        Тест: Взаимный лайк создает матч.
        """
        # user1 лайкает user2
        url1 = reverse('dating_app:like_dislike', kwargs={'user_id': self.user2.id})
        data1 = {'vote': 1}
        self.client.post(url1, data1, format='json')

        # Авторизуем user2
        self.client.force_authenticate(user=self.user2)
        # user2 лайкает user1
        url2 = reverse('dating_app:like_dislike', kwargs={'user_id': self.user1.id})
        data2 = {'vote': 1}
        response2 = self.client.post(url2, data2, format='json')

        # Проверяем, что матч создан
        from .models import Match
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(Match.objects.count(), 1)
        match = Match.objects.first()
        # Проверяем, что оба пользователя участвуют в матче
        self.assertTrue(match.user1 in [self.user1, self.user2])
        self.assertTrue(match.user2 in [self.user1, self.user2])
        self.assertNotEqual(match.user1, match.user2)

    def test_like_self(self):
        """
        Тест: Пользователь не может лайкнуть/дизлайкнуть себя.
        """
        url = reverse('dating_app:like_dislike', kwargs={'user_id': self.user1.id})
        data = {'vote': 1}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(LikeDislike.objects.count(), 0)
        self.assertIn('не можете оценить', response.data['error'])