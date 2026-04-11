#!/bin/sh
set -e

echo "Waiting for redis"

REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
BLOG_SEED_DB="${BLOG_SEED_DB:-False}"

while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  sleep 1
done

echo "Redis is up"

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py compilemessages

if [ "$BLOG_SEED_DB" = "true" ]; then
  python manage.py seed_db
else
  echo "Skipping seeding"
fi

exec "$@"