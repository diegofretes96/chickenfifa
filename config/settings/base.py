"""
Configuración base compartida por todos los entornos.
"""
from pathlib import Path

import environ

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    PREDICTION_LOCK_MINUTES=(int, 30),
)
environ.Env.read_env(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "django_htmx",
    "django_celery_results",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.tournament",
    "apps.predictions",
    "apps.leaderboard",
    "apps.bets",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.tournament.context_processors.tournament_context",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "auth.User"
LOGIN_URL = "/cuentas/iniciar-sesion/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/cuentas/iniciar-sesion/"

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Asuncion"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("es", "Español"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# ---------------------------------------------------------------------------
# Static & Media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [d for d in [BASE_DIR / "static"] if d.exists()]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# ---------------------------------------------------------------------------
# Default primary key
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Crispy Forms
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# ---------------------------------------------------------------------------
# Domain logic: FIFA 2026
# ---------------------------------------------------------------------------
# Minutos antes del partido en que se bloquean los pronósticos
PREDICTION_LOCK_MINUTES = env("PREDICTION_LOCK_MINUTES")

TOURNAMENT_STAGES = [
    ("grupo", "Fase de Grupos"),
    ("dieciseisavos", "Dieciseisavos de Final"),
    ("octavos", "Octavos de Final"),
    ("cuartos", "Cuartos de Final"),
    ("semifinal", "Semifinal"),
    ("tercero", "Tercer Puesto"),
    ("final", "Final"),
]

FIFA_2026_GROUPS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
