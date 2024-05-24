from django.conf import settings
from django.middleware import csrf


def htmx_context(_request):
    return {
        "WEBPACK_ENABLED": settings.WEBPACK_STATS_FILE.exists(),
        "csrf_token": csrf.get_token(_request)
    }
