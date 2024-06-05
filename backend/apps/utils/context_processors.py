from django.conf import settings
# from django.middleware import csrf


def htmx_context(_request):
    return {
        "WEBPACK_ENABLED": False, # settings.DEBUG,
        "csrf_token": "", # csrf.get_token(_request)
    }
