from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from apps.users.token_views import DocumentedTokenRefreshView, DocumentedTokenVerifyView
from apps.blog.views import PostViewSet, PostCommentCreateAPIView
from apps.users.views import (
    CustomTokenView,
    RegisterViewSet,
    UserLanguageView,
    UserPreferencesView,
    UserTimezoneView,
)
from apps.blog.stat_views import stats_view
from apps.blog.sse import sse_posts_stream_view


def home(request):
    return HttpResponse("OK")


router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="posts")

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),

    path("api/schema/", SpectacularAPIView.as_view(), name='schema'),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name='swagger-ui'),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name='redoc'),

    path("api/auth/register/", RegisterViewSet.as_view({"post": "create"}), name="register"),
    path("api/auth/token/", CustomTokenView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", DocumentedTokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", DocumentedTokenVerifyView.as_view(), name="token_verify"),

    path("api/me/preferences/", UserPreferencesView.as_view(), name="user_preferences"),
    path("api/auth/language/", UserLanguageView.as_view(), name="user_language"),
    path("api/auth/timezone/", UserTimezoneView.as_view(), name="user_timezone"),
    path("api/me/language/", UserLanguageView.as_view(), name="user_language_legacy"),
    path("api/me/timezone/", UserTimezoneView.as_view(), name="user_timezone_legacy"),

    path("api/", include(router.urls)),
    path("api/stats/", stats_view, name="stats"),

    path("posts/<slug:slug>/comments/", PostCommentCreateAPIView.as_view(), name="post-comments-create"),

    path("/api/posts/stream/", sse_posts_stream_view, name="posts-stream")

]