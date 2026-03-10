from django.conf import settings
from django.utils import translation
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


def get_language_from_authenticated_user(request):
    try:
        auth = JWTAuthentication()
        result = auth.authenticate(request)
        if not result:
            return None

        user, token = result
        request.user = user
        request.auth = token

        language = getattr(user, "preferred_language", None)
        return normalize_language_code(language)
    except Exception:
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


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = (
                get_language_from_authenticated_user(request)
                or get_language_from_query(request)
                or get_language_from_header(request)
                or settings.LANGUAGE_CODE
        )
        translation.activate(language)
        request.LANGUAGE_CODE = language

        response = self.get_response(request)
        response["Content-Language"] = language

        translation.deactivate()
        return response
