# dating_app/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, Interest, LikeDislike, ViewHistory, LikedUsers, DislikedUsers, LikeHistory, Match

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email'] # Поле email можно сделать read_only или обработать отдельно при регистрации

class InterestSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Interest.
    """
    class Meta:
        model = Interest
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели UserProfile.
    """
    user = UserSerializer(read_only=True)
    age = serializers.SerializerMethodField() # Поле для возраста
    full_name = serializers.SerializerMethodField() # Поле для полного имени
    interests = InterestSerializer(many=True, read_only=True) # Вложенный вывод увлечений

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'first_name', 'last_name', 'patronymic', 'age', 'full_name',
            'gender', 'birth_date', 'city', 'interests', 'status', 'photo_gallery', 'main_photo',
            'likes_count', 'privacy_setting'
        ]
        read_only_fields = ['id', 'user', 'age', 'full_name', 'interests', 'likes_count']

    def get_age(self, obj):
        return obj.get_age()

    def get_full_name(self, obj):
        return obj.get_full_name()

class LikeDislikeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели LikeDislike.
    """
    class Meta:
        model = LikeDislike
        fields = ['id', 'voter', 'target_user', 'vote', 'timestamp']
        read_only_fields = ['id', 'voter', 'timestamp'] # voter заполняется автоматически, timestamp авто

class ViewHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели ViewHistory.
    """
    class Meta:
        model = ViewHistory
        fields = ['id', 'viewer', 'viewed_profile', 'timestamp']
        read_only_fields = ['id', 'viewer', 'timestamp'] # viewer заполняется автоматически

class LikedUsersSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели LikedUsers.
    """
    class Meta:
        model = LikedUsers
        fields = ['id', 'user', 'liked_user', 'timestamp']
        read_only_fields = ['id', 'user', 'timestamp'] # user заполняется автоматически

class DislikedUsersSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели DislikedUsers.
    """
    class Meta:
        model = DislikedUsers
        fields = ['id', 'user', 'disliked_user', 'timestamp']
        read_only_fields = ['id', 'user', 'timestamp'] # user заполняется автоматически

class LikeHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели LikeHistory.
    """
    class Meta:
        model = LikeHistory
        fields = ['id', 'user', 'target_user', 'timestamp']
        read_only_fields = ['id', 'user', 'timestamp'] # user заполняется автоматически

class MatchSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Match.
    """
    class Meta:
        model = Match
        fields = ['id', 'user1', 'user2', 'timestamp']
        read_only_fields = ['id', 'timestamp'] # user1 и user2 заполняются при создании