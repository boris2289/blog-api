from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.utils import formats, timezone


def get_request_timezone(request):
    if getattr(request, "user", None) and request.user.is_authenticated:
        timezone_name = getattr(request.user, "timezone", "UTC") or "UTC"
    else:
        timezone_name = "UTC"
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def format_localized_datetime(value, request):
    if value is None:
        return None

    tz = get_request_timezone(request)
    localized_value = timezone.localtime(value, tz)
    return formats.date_format(localized_value, format="DATETIME_FORMAT", use_l10n=True)
