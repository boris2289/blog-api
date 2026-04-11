import os
from celery import Celery

env_id = os.getenv("BLOG_ENV_ID", "local").lower().strip()
if env_id == "prod":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.env.prod")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.env.local")

app = Celery("settings")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()