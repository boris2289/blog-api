from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone, translation
from rest_framework_simplejwt.authentication import JWTAuthentication

SUPPORTED_LANGUAGES = {code for code, _ in settings.LANGUAGES}


def normalize_language_code(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower()
    short = value.split('-')[0]
    if short in SUPPORTED_LANGUAGES:
        return short
    return None


def get_authenticated_user(request):
    try:
        auth = JWTAuthentication()
        result = auth.authenticate(request)
        if not result:
            return None

        user, token = result
        request.user = user
        request.auth = token
        return user
    except Exception:
        return None


def get_language_from_authenticated_user(request):
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        return normalize_language_code(getattr(user, "preferred_language", None))
    return None


def get_language_from_query(request):
    return normalize_language_code(request.GET.get("lang"))


def get_language_from_header(request):
    header = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    if not header:
        return None

    for item in header.split(","):
        candidate = item.split(";")[0].strip()
        normalized = normalize_language_code(candidate)
        if normalized:
            return normalized
    return None


def get_timezone_from_authenticated_user(request):
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None

    timezone_name = getattr(user, "timezone", None) or settings.TIME_ZONE
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(settings.TIME_ZONE)


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        get_authenticated_user(request)

        language = (
            get_language_from_query(request)
            or get_language_from_authenticated_user(request)
            or get_language_from_header(request)
            or settings.LANGUAGE_CODE
        )
        translation.activate(language)
        request.LANGUAGE_CODE = language

        active_timezone = get_timezone_from_authenticated_user(request)
        if active_timezone is not None:
            timezone.activate(active_timezone)
        else:
            timezone.deactivate()

        response = self.get_response(request)
        response["Content-Language"] = language

        translation.deactivate()
        timezone.deactivate()
        return response