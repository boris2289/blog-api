from django.urls import path

from apps.notifications.consumers import CommentConsumer

websocket_urlpatterns = [
    path(f"ws/posts/<slug>/comments/", CommentConsumer.as_asgi())
]
