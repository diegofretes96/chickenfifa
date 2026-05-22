"""
Configuración de Celery para ChickenFifa.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("chickenfifa")

# Cargar configuración de Django settings (prefijo CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-descubrir tareas en todos los apps instalados
app.autodiscover_tasks()
