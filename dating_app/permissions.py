# dating_app/permissions.py

from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Пользовательские права доступа.
    Позволяет только владельцам профиля редактировать или удалять его.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем чтение (GET, HEAD, OPTIONS) всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем редактирование/удаление только владельцу профиля
        # Предполагаем, что у модели есть атрибут 'user', указывающий на владельца
        # В случае UserProfile, это будет obj.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Если у объекта нет атрибута 'user', проверяем, является ли он экземпляром User
        elif hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        return False