#!/bin/sh
# =============================================================================
# entrypoint.sh — ChickenFifa
# Ejecutado como punto de entrada del contenedor Docker.
# Maneja migraciones, archivos estáticos y el inicio de Gunicorn o Celery.
# =============================================================================
set -e

echo "==> [ChickenFifa] Iniciando entrypoint..."

# Esperar a que la base de datos esté disponible
echo "==> Esperando a la base de datos..."
python << 'PYEOF'
import os
import time
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from django.db import connection
from django.db.utils import OperationalError

retries = 30
while retries > 0:
    try:
        connection.ensure_connection()
        print("    Base de datos disponible.")
        break
    except OperationalError:
        retries -= 1
        print(f"    DB no disponible. Reintentando... ({retries} intentos restantes)")
        time.sleep(2)
else:
    print("ERROR: No se pudo conectar a la base de datos. Abortando.")
    exit(1)
PYEOF

# Solo el servidor web ejecuta migraciones, static y superusuario
if [ "$1" = "gunicorn" ]; then
    echo "==> Ejecutando migraciones..."
    python manage.py migrate --noinput

    echo "==> Recopilando archivos estáticos..."
    python manage.py collectstatic --noinput --clear

    if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        echo "==> Creando superusuario si no existe..."
        python manage.py createsuperuser \
            --noinput \
            --username "${DJANGO_SUPERUSER_USERNAME:-admin}" \
            --email "$DJANGO_SUPERUSER_EMAIL" \
            2>/dev/null || echo "    Superusuario ya existe, omitiendo."
    fi
fi

echo "==> Entrypoint completado."

# Decidir qué proceso iniciar según el argumento CMD
case "$1" in
    gunicorn)
        echo "==> Iniciando Gunicorn en 0.0.0.0:${PORT:-8000}..."
        exec gunicorn config.wsgi:application \
            --bind "0.0.0.0:${PORT:-8000}" \
            --workers "${GUNICORN_WORKERS:-3}" \
            --worker-class sync \
            --timeout 120 \
            --keep-alive 5 \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            --log-level "${GUNICORN_LOG_LEVEL:-info}" \
            --access-logfile - \
            --error-logfile -
        ;;
    celery)
        echo "==> Iniciando Celery worker..."
        exec celery -A config worker \
            --loglevel="${CELERY_LOG_LEVEL:-info}" \
            --concurrency="${CELERY_CONCURRENCY:-2}"
        ;;
    celery-beat)
        echo "==> Iniciando Celery beat..."
        exec celery -A config beat \
            --loglevel="${CELERY_LOG_LEVEL:-info}" \
            --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;
    *)
        echo "==> Ejecutando comando personalizado: $@"
        exec "$@"
        ;;
esac
