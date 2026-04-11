from decouple import config

BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")
SECRET_KEY = config("BLOG_SECRET_KEY")
DEBUG_FLAG = config("BLOG_DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = [
    h.strip()
    for h in config("BLOG_ALLOWED_HOSTS", default="").split(",")
    if h.strip()
]

DB_NAME = config("BLOG_DB_NAME", default="")
DB_USER = config("BLOG_DB_USER", default="")
DB_PASSWORD = config("BLOG_DB_PASSWORD", default="")
DB_HOST = config("BLOG_DB_HOST", default="db")
DB_PORT = config("BLOG_DB_PORT", default=5432, cast=int)

REDIS_HOST = config("REDIS_HOST", default="redis", cast=str)
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)
REDIS_CELERY_DB = config("REDIS_CELERY_DB", default=0, cast=int)
REDIS_DB = config("REDIS_DB", default=1, cast=int)

CHANNEL_REDIS_HOST = REDIS_HOST
CHANNEL_REDIS_PORT = REDIS_PORT

BLOG_REDIS_URL = config("BLOG_REDIS_URL", default="redis://redis:6379/0")
BLOG_CELERY_BROKER_URL = config("BLOG_CELERY_BROKER_URL", default="redis://redis:6379/1")
BLOG_CELERY_RESULT_BACKEND = config(
    "BLOG_CELERY_RESULT_BACKEND",
    default="redis://redis:6379/1",
)

CELERY_BROKER_URL = BLOG_CELERY_BROKER_URL
CELERY_RESULT_BACKEND = BLOG_CELERY_RESULT_BACKEND