from decouple import Config, RepositoryEnv

config = Config(RepositoryEnv("settings/.env"))

BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")
SECRET_KEY = config("BLOG_SECRET_KEY")
DEBUG_FLAG = config("BLOG_DEBUG", default=False, cast=bool)
CHANNEL_REDIS_HOST = config("127.0.0.1", 6379)

ALLOWED_HOSTS = [
    h.strip()
    for h in config("BLOG_ALLOWED_HOSTS", default="").split(",")
    if h.strip()
]

DB_NAME = config("BLOG_DB_NAME", default="")
DB_USER = config("BLOG_DB_USER", default="")
DB_PASSWORD = config("BLOG_DB_PASSWORD", default="")
DB_HOST = config("BLOG_DB_HOST", default="")
DB_PORT = config("BLOG_DB_PORT", default="5432")