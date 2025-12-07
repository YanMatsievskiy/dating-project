# dating_app/views.py

from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Q, Count # Для сложных фильтров
from .models import UserProfile, Interest, LikeDislike, ViewHistory, LikedUsers, DislikedUsers, LikeHistory, Match
from .serializers import (
    UserSerializer, UserProfileSerializer, InterestSerializer, LikeDislikeSerializer,
    ViewHistorySerializer, LikedUsersSerializer, DislikedUsersSerializer, LikeHistorySerializer, MatchSerializer
)
from .permissions import IsOwnerOrReadOnly # Предполагаем, что вы создали этот класс

User = get_user_model()

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для просмотра пользователей (только профили).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # Только для авторизованных пользователей

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint для просмотра, создания, обновления и удаления профилей пользователей.
    """
    queryset = UserProfile.objects.select_related('user').prefetch_related('interests').all() # Оптимизация запросов
    serializer_class = UserProfileSerializer
    permission_classes = [IsOwnerOrReadOnly] # Только владелец может изменять/удалять

    # Добавляем фильтрацию по полу, возрасту, городу, статусу, увлечениям
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'city', 'status', 'interests__name']
    search_fields = ['first_name', 'last_name', 'patronymic', 'city', 'interests__name']
    ordering_fields = ['birth_date', 'likes_count']

    def get_queryset(self):
        """
        Оптимизированный queryset с фильтрацией по возрасту.
        """
        queryset = super().get_queryset()
        # Фильтрация по возрасту (например, ?min_age=20&max_age=30)
        min_age = self.request.query_params.get('min_age', None)
        max_age = self.request.query_params.get('max_age', None)
        if min_age is not None:
            try:
                min_age_int = int(min_age)
                # Вычисляем дату рождения, соответствующую минимальному возрасту
                from datetime import date, timedelta
                birth_date_threshold_min = date.today() - timedelta(days=min_age_int * 365.25) # Приблизительно
                queryset = queryset.filter(birth_date__lte=birth_date_threshold_min)
            except ValueError:
                pass # Игнорируем некорректное значение
        if max_age is not None:
            try:
                max_age_int = int(max_age)
                # Вычисляем дату рождения, соответствующую максимальному возрасту
                birth_date_threshold_max = date.today() - timedelta(days=max_age_int * 365.25) # Приблизительно
                queryset = queryset.filter(birth_date__gte=birth_date_threshold_max)
            except ValueError:
                pass # Игнорируем некорректное значение

        # Исключаем текущего пользователя из списка (для поиска)
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(user=self.request.user)

        return queryset

class InterestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint только для просмотра увлечений.
    """
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = [IsAuthenticated] # Только для авторизованных пользователей

# --- Система взаимодействий ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_dislike(request, user_id):
    """
    Обработка лайка/дизлайка.
    """
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    if request.user == target_user:
        return Response({'error': 'Вы не можете оценить свой собственный профиль'}, status=status.HTTP_400_BAD_REQUEST)

    vote_value = request.data.get('vote') # Ожидаем 1 (лайк) или -1 (дизлайк)
    if vote_value not in [LikeDislike.LIKE, LikeDislike.DISLIKE]:
        return Response({'error': 'Некорректное значение голоса. Используйте 1 (лайк) или -1 (дизлайк).'}, status=status.HTTP_400_BAD_REQUEST)

    # Проверяем, есть ли уже голос
    existing_vote = LikeDislike.objects.filter(voter=request.user, target_user=target_user).first()

    if existing_vote:
        # Если голос уже был, обновляем его
        if existing_vote.vote == vote_value:
            # Если голос не изменился, просто возвращаем сообщение
            return Response({'message': 'Голос не изменился.'})
        else:
            # Если голос изменился (например, с дизлайка на лайк), меняем значение
            existing_vote.vote = vote_value
            existing_vote.save()
    else:
        # Если голоса не было, создаем новый
        LikeDislike.objects.create(voter=request.user, target_user=target_user, vote=vote_value)

    # Проверяем, есть ли взаимный лайк (матч)
    mutual_like = LikeDislike.objects.filter(
        voter=target_user,
        target_user=request.user,
        vote=LikeDislike.LIKE
    ).exists()

    if vote_value == LikeDislike.LIKE and mutual_like:
        # Создаем матч
        match, created = Match.objects.get_or_create(
            user1=min(request.user, target_user, key=lambda u: u.id),
            user2=max(request.user, target_user, key=lambda u: u.id)
        )
        if created:
            # Здесь можно отправить уведомление о матче (через WebSocket или email)
            return Response({'message': 'Взаимный лайк! Вы можете обменяться контактами!', 'match_created': True})

    return Response({'message': 'Голос учтен.'})

# --- Дополнительные функции профиля ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_random_profile(request):
    """
    Возвращает случайный профиль, соответствующий фильтрам (пол, возраст, город, статус).
    """
    # Получаем параметры фильтрации из запроса
    gender_filter = request.query_params.get('gender', None)
    city_filter = request.query_params.get('city', None)
    status_filter = request.query_params.get('status', None)
    min_age_filter = request.query_params.get('min_age', None)
    max_age_filter = request.query_params.get('max_age', None)

    # Начинаем с queryset всех профилей, кроме текущего пользователя
    queryset = UserProfile.objects.select_related('user').exclude(user=request.user)

    # Применяем фильтры
    if gender_filter:
        queryset = queryset.filter(gender=gender_filter)
    if city_filter:
        queryset = queryset.filter(city=city_filter)
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Фильтрация по возрасту (аналогично в UserProfileViewSet)
    if min_age_filter:
        try:
            min_age_int = int(min_age_filter)
            from datetime import date, timedelta
            birth_date_threshold_min = date.today() - timedelta(days=min_age_int * 365.25)
            queryset = queryset.filter(birth_date__lte=birth_date_threshold_min)
        except ValueError:
            pass
    if max_age_filter:
        try:
            max_age_int = int(max_age_filter)
            from datetime import date, timedelta
            birth_date_threshold_max = date.today() - timedelta(days=max_age_int * 365.25)
            queryset = queryset.filter(birth_date__gte=birth_date_threshold_max)
        except ValueError:
            pass

    # Исключаем пользователей, которых текущий пользователь уже лайкнул или дизлайкнул
    voted_users_ids = LikeDislike.objects.filter(voter=request.user).values_list('target_user_id', flat=True)
    queryset = queryset.exclude(user_id__in=voted_users_ids)

    # Исключаем пользователей, чьи профили приватные (или требуют особого разрешения)
    # (Предположим, что приватность проверяется в другом месте или через permission_classes)
    # queryset = queryset.filter(privacy_setting='public') # Пример простой фильтрации

    # Получаем случайный профиль
    import random
    profiles_list = list(queryset)
    if profiles_list:
        random_profile = random.choice(profiles_list)

        # Записываем в историю просмотров
        ViewHistory.objects.create(viewer=request.user, viewed_profile=random_profile)

        serializer = UserProfileSerializer(random_profile)
        return Response(serializer.data)
    else:
        return Response({'message': 'Подходящих профилей не найдено.'}, status=status.HTTP_404_NOT_FOUND)

# --- (Опционально) Представления для истории и списков ---
class ViewHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для просмотра истории просмотров профилей.
    """
    serializer_class = ViewHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ViewHistory.objects.filter(viewer=self.request.user).select_related('viewed_profile__user')

class LikedUsersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для просмотра списка понравившихся пользователей.
    """
    serializer_class = LikedUsersSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LikedUsers.objects.filter(user=self.request.user).select_related('liked_user')

class DislikedUsersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для просмотра списка непонравившихся пользователей.
    """
    serializer_class = DislikedUsersSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DislikedUsers.objects.filter(user=self.request.user).select_related('disliked_user')

class LikeHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для просмотра истории лайков пользователя.
    """
    serializer_class = LikeHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LikeHistory.objects.filter(user=self.request.user).select_related('target_user')

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для просмотра матчей (взаимных лайков).
    """
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только матчи, в которых участвует текущий пользователь
        return Match.objects.filter(Q(user1=self.request.user) | Q(user2=self.request.user)).select_related('user1', 'user2')