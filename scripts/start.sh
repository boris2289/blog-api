#!/usr/bin/env bash
set -Eeuo pipefail

CURRENT_STEP="startup"
SERVER_PID=""

on_error() {
  local exit_code=$?
  echo ""
  echo "ERROR: Step failed: ${CURRENT_STEP}" >&2
  exit "${exit_code}"
}

cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
  fi
}

trap on_error ERR
trap cleanup EXIT INT TERM

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${PROJECT_ROOT}/.venv"
ENV_FILE_ROOT="${PROJECT_ROOT}/.env"
ENV_FILE_SETTINGS="${PROJECT_ROOT}/settings/.env"

SUPERUSER_EMAIL="admin@example.com"
SUPERUSER_PASSWORD="admin12345"
SUPERUSER_FIRST_NAME="Admin"
SUPERUSER_LAST_NAME="User"

step() {
  CURRENT_STEP="$1"
  echo ""
  echo "==> ${CURRENT_STEP}"
}

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

step "Checking .env file"

if [[ -f "${ENV_FILE_ROOT}" ]]; then
  ACTIVE_ENV_FILE="${ENV_FILE_ROOT}"
elif [[ -f "${ENV_FILE_SETTINGS}" ]]; then
  ACTIVE_ENV_FILE="${ENV_FILE_SETTINGS}"
else
  fail ".env file not found. Create either .env in the project root or settings/.env."
fi

set -a
# shellcheck disable=SC1090
source "${ACTIVE_ENV_FILE}"
set +a

mkdir -p settings
if [[ "${ACTIVE_ENV_FILE}" == "${ENV_FILE_ROOT}" ]]; then
  cp "${ENV_FILE_ROOT}" "${ENV_FILE_SETTINGS}"
fi

REQUIRED_VARS=(
  "BLOG_SECRET_KEY"
  "BLOG_ENV_ID"
  "BLOG_DEBUG"
  "BLOG_ALLOWED_HOSTS"
)

for var_name in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required environment variable: ${var_name}" >&2
    exit 1
  fi
done

step "Creating virtual environment"
if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

step "Installing dependencies"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements/base.txt

export DJANGO_SETTINGS_MODULE="settings.env.local"

step "Preparing directories"
mkdir -p logs staticfiles

step "Running migrations"
python manage.py migrate

step "Collecting static files"
python manage.py collectstatic --noinput

step "Compiling translation files"
if ! command -v msgfmt >/dev/null 2>&1; then
  fail "gettext is required for compilemessages. Install it first (for example: brew install gettext)."
fi
python manage.py compilemessages

step "Creating superuser"
python manage.py shell <<PY
from django.contrib.auth import get_user_model

User = get_user_model()
email = "${SUPERUSER_EMAIL}"

defaults = {
    "first_name": "${SUPERUSER_FIRST_NAME}",
    "last_name": "${SUPERUSER_LAST_NAME}",
}

user, created = User.objects.get_or_create(email=email, defaults=defaults)

changed = False
if user.first_name != "${SUPERUSER_FIRST_NAME}":
    user.first_name = "${SUPERUSER_FIRST_NAME}"
    changed = True
if user.last_name != "${SUPERUSER_LAST_NAME}":
    user.last_name = "${SUPERUSER_LAST_NAME}"
    changed = True
if not user.is_staff:
    user.is_staff = True
    changed = True
if not user.is_superuser:
    user.is_superuser = True
    changed = True
if not user.is_active:
    user.is_active = True
    changed = True

field_names = {f.name for f in user._meta.fields}

if "preferred_language" in field_names and getattr(user, "preferred_language", None) != "en":
    user.preferred_language = "en"
    changed = True

if "timezone" in field_names and getattr(user, "timezone", None) != "UTC":
    user.timezone = "UTC"
    changed = True

user.set_password("${SUPERUSER_PASSWORD}")
changed = True

if changed:
    user.save()

print("Superuser ready:", email)
PY

step "Seeding database with realistic test data"
python manage.py shell <<'PY'
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

from apps.blog.models import Category, Tag, Post, Comment

User = get_user_model()

user_field_names = {f.name for f in User._meta.fields}
category_field_names = {f.name for f in Category._meta.fields}

users_data = [
    {
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Ivanova",
        "password": "testpass123",
        "preferred_language": "ru",
        "timezone": "Asia/Almaty",
    },
    {
        "email": "bob@example.com",
        "first_name": "Bob",
        "last_name": "Smith",
        "password": "testpass123",
        "preferred_language": "en",
        "timezone": "UTC",
    },
    {
        "email": "amira@example.com",
        "first_name": "Amira",
        "last_name": "Nurgalieva",
        "password": "testpass123",
        "preferred_language": "kk",
        "timezone": "Asia/Almaty",
    },
    {
        "email": "daniyar@example.com",
        "first_name": "Daniyar",
        "last_name": "Sarsenov",
        "password": "testpass123",
        "preferred_language": "ru",
        "timezone": "Europe/Moscow",
    },
]

created_users = []

for item in users_data:
    defaults = {
        "first_name": item["first_name"],
        "last_name": item["last_name"],
        "is_active": True,
    }

    user, _ = User.objects.get_or_create(email=item["email"], defaults=defaults)

    updated = False
    if user.first_name != item["first_name"]:
        user.first_name = item["first_name"]
        updated = True
    if user.last_name != item["last_name"]:
        user.last_name = item["last_name"]
        updated = True
    if not user.is_active:
        user.is_active = True
        updated = True

    if "preferred_language" in user_field_names and getattr(user, "preferred_language", None) != item["preferred_language"]:
        user.preferred_language = item["preferred_language"]
        updated = True

    if "timezone" in user_field_names and getattr(user, "timezone", None) != item["timezone"]:
        user.timezone = item["timezone"]
        updated = True

    user.set_password(item["password"])
    updated = True

    if updated:
        user.save()

    created_users.append(user)

categories_data = [
    {
        "slug": "news",
        "name": "News",
        "name_en": "News",
        "name_ru": "Новости",
        "name_kk": "Жаңалықтар",
    },
    {
        "slug": "technology",
        "name": "Technology",
        "name_en": "Technology",
        "name_ru": "Технологии",
        "name_kk": "Технология",
    },
    {
        "slug": "education",
        "name": "Education",
        "name_en": "Education",
        "name_ru": "Образование",
        "name_kk": "Білім",
    },
    {
        "slug": "lifestyle",
        "name": "Lifestyle",
        "name_en": "Lifestyle",
        "name_ru": "Образ жизни",
        "name_kk": "Өмір салты",
    },
]

categories = []
for item in categories_data:
    defaults = {"name": item["name"]}
    category, _ = Category.objects.get_or_create(slug=item["slug"], defaults=defaults)

    changed = False
    if hasattr(category, "name") and category.name != item["name"]:
        category.name = item["name"]
        changed = True

    if "name_en" in category_field_names and getattr(category, "name_en", "") != item["name_en"]:
        category.name_en = item["name_en"]
        changed = True
    if "name_ru" in category_field_names and getattr(category, "name_ru", "") != item["name_ru"]:
        category.name_ru = item["name_ru"]
        changed = True
    if "name_kk" in category_field_names and getattr(category, "name_kk", "") != item["name_kk"]:
        category.name_kk = item["name_kk"]
        changed = True

    if changed:
        category.save()

    categories.append(category)

tag_names = [
    "python",
    "django",
    "api",
    "redis",
    "localization",
    "swagger",
    "redoc",
    "testing",
    "backend",
    "async",
]

tags = []
for tag_name in tag_names:
    tag, _ = Tag.objects.get_or_create(
        slug=slugify(tag_name),
        defaults={"name": tag_name},
    )
    if tag.name != tag_name:
        tag.name = tag_name
        tag.save(update_fields=["name"])
    tags.append(tag)

published_count = 120
draft_count = 12
archived_like_count = 8  # still draft, but different content themes

all_posts = []

for idx in range(1, published_count + 1):
    author = created_users[(idx - 1) % len(created_users)]
    category = categories[(idx - 1) % len(categories)]

    post, _ = Post.objects.update_or_create(
        slug=f"seed-post-{idx}",
        defaults={
            "author": author,
            "title": f"Seed published post #{idx}",
            "body": (
                f"This is seeded published post number {idx}. "
                f"It exists to test pagination, localization, caching, and documentation."
            ),
            "category": category,
            "status": "published",
        },
    )
    post.tags.set([tags[idx % len(tags)], tags[(idx + 1) % len(tags)]])
    all_posts.append(post)

for idx in range(1, draft_count + 1):
    author = created_users[(idx - 1) % len(created_users)]
    category = categories[(idx - 1) % len(categories)]

    post, _ = Post.objects.update_or_create(
        slug=f"draft-post-{idx}",
        defaults={
            "author": author,
            "title": f"Seed draft post #{idx}",
            "body": f"This is draft post number {idx}.",
            "category": category,
            "status": "draft",
        },
    )
    post.tags.set([tags[idx % len(tags)]])
    all_posts.append(post)

for idx in range(1, archived_like_count + 1):
    author = created_users[(idx - 1) % len(created_users)]
    category = categories[(idx - 1) % len(categories)]

    post, _ = Post.objects.update_or_create(
        slug=f"review-post-{idx}",
        defaults={
            "author": author,
            "title": f"Review queue post #{idx}",
            "body": f"This seeded post simulates content waiting for moderation #{idx}.",
            "category": category,
            "status": "draft",
        },
    )
    post.tags.set([tags[(idx + 2) % len(tags)]])
    all_posts.append(post)

seed_comment_posts = Post.objects.filter(slug__startswith="seed-post-").order_by("id")[:20]
Comment.objects.filter(post__in=seed_comment_posts, body__startswith="[seed]").delete()

for idx, post in enumerate(seed_comment_posts, start=1):
    author_one = created_users[idx % len(created_users)]
    author_two = created_users[(idx + 1) % len(created_users)]

    Comment.objects.create(
        post=post,
        author=author_one,
        body=f"[seed] Great post #{idx}. Useful for testing comments.",
    )
    Comment.objects.create(
        post=post,
        author=author_two,
        body=f"[seed] Second opinion for post #{idx}.",
    )

print("Seed complete.")
print("Users:", User.objects.count())
print("Categories:", Category.objects.count())
print("Tags:", Tag.objects.count())
print("Posts:", Post.objects.count())
print("Comments:", Comment.objects.count())
PY

step "Starting development server"
python manage.py runserver 127.0.0.1:8000 &
SERVER_PID=$!

sleep 2

if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
  fail "Development server failed to start."
fi

echo ""
echo "========================================"
echo "Project is running"
echo "API:          http://127.0.0.1:8000/api/"
echo "Swagger UI:   http://127.0.0.1:8000/api/docs/"
echo "ReDoc:        http://127.0.0.1:8000/api/redoc/"
echo "Admin:        http://127.0.0.1:8000/admin/"
echo ""
echo "Superuser credentials:"
echo "Email:        ${SUPERUSER_EMAIL}"
echo "Password:     ${SUPERUSER_PASSWORD}"
echo "========================================"
echo ""

wait "${SERVER_PID}"