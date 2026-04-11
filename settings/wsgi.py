"""
WSGI config for settings project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

env_id = os.getenv("BLOG_ENV_ID", "local").lower().strip()
if env_id == "prod":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.env.prod")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.env.local")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
