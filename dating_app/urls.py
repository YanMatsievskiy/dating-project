# dating_app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.UserProfileViewSet, basename='userprofile')
router.register(r'interests', views.InterestViewSet, basename='interest')
router.register(r'view-history', views.ViewHistoryViewSet, basename='viewhistory')
router.register(r'liked-users', views.LikedUsersViewSet, basename='likedusers')
router.register(r'disliked-users', views.DislikedUsersViewSet, basename='dislikedusers')
router.register(r'like-history', views.LikeHistoryViewSet, basename='likehistory')
router.register(r'matches', views.MatchViewSet, basename='match')

app_name = 'dating_app'

urlpatterns = [
    # API маршруты DRF
    path('api/', include(router.urls)),
    # JWT токены
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Маршруты для документации (Swagger)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Маршрут для лайка/дизлайка
    path('api/like-dislike/<int:user_id>/', views.like_dislike, name='like_dislike'),
    # Маршрут для получения случайного профиля
    path('api/random-profile/', views.get_random_profile, name='get_random_profile'),
]