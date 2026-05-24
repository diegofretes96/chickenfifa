"""
Configuración para desarrollo local.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405
except ImportError:
    pass

try:
    import django_extensions  # noqa: F401
    INSTALLED_APPS += ["django_extensions"]  # noqa: F405
except ImportError:
    pass

INTERNAL_IPS = ["127.0.0.1"]

# En local puede usar consola como email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
