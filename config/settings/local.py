"""
Configuración para desarrollo local.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

INSTALLED_APPS += ["debug_toolbar", "django_extensions"]  # noqa: F405

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

# En local puede usar consola como email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
