from ..base import *
from ..conf import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}

ALLOWED_HOSTS = [

    host.strip()

    for host in os.getenv(

        "BLOG_ALLOWED_HOSTS",

        "localhost,127.0.0.1,0.0.0.0,web,nginx"

    ).split(",")

    if host.strip()

]