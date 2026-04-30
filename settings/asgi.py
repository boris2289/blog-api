import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

env_id = os.getenv("BLOG_ENV_ID", "local").lower().strip()

if env_id == "prod":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.env.prod")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.env.local")

django_asgi_app = get_asgi_application()

from apps.notifications.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    }
)