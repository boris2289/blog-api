#!/bin/sh
set -e

MIGRATIONS_FLAG="/app/data/.migrations_done"

echo "Waiting for redis"
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is up"

if [ "$WAIT_FOR_MIGRATIONS" = "true" ]; then
  echo "Waiting for migrations flag: $MIGRATIONS_FLAG"

  while [ ! -f "$MIGRATIONS_FLAG" ]; do
    sleep 1
  done

  echo "Migrations flag found"
fi

if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Running migrations"

  # на всякий случай удаляем старый флаг перед новой миграцией
  rm -f "$MIGRATIONS_FLAG"

  python manage.py migrate --noinput

  echo "Migrations completed"

  # ВАЖНО: создаём флаг СРАЗУ после миграций,
  # а не после collectstatic/compilemessages/seed
  mkdir -p /app/data
  touch "$MIGRATIONS_FLAG"

  echo "Migrations flag created: $MIGRATIONS_FLAG"
else
  echo "Skipping migrations"
fi

if [ "$RUN_COLLECTSTATIC" = "true" ]; then
  echo "Collecting static files"
  python manage.py collectstatic --noinput
else
  echo "Skipping collectstatic"
fi

if [ "$RUN_COMPILEMESSAGES" = "true" ]; then
  echo "Compiling messages"
  python manage.py compilemessages || true
else
  echo "Skipping compilemessages"
fi

if [ "$BLOG_SEED_DB" = "true" ]; then
  echo "Seeding database"
  python manage.py seed_db || true
else
  echo "Skipping seeding"
fi

exec "$@"