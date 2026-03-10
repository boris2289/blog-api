from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.blog.views import PostViewSet
from apps.users.views import (
    CustomTokenView,
    RegisterViewSet,
    UserLanguageView,
    UserPreferencesView,
    UserTimezoneView,
)


def home(request):
    return HttpResponse("OK")


router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="posts")

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),

    path("api/auth/register/", RegisterViewSet.as_view({"post": "create"}), name="register"),
    path("api/auth/token/", CustomTokenView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/me/preferences/", UserPreferencesView.as_view(), name="user_preferences"),

    path("api/me/language/", UserLanguageView.as_view(), name="user_language"),
    path("api/me/timezone/", UserTimezoneView.as_view(), name="user_timezone"),

    path("api/", include(router.urls)),
]