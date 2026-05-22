# =============================================================================
# ChickenFifa — Dockerfile multietapa (Python 3.12-slim)
# Etapa 1: builder  → instala dependencias en un venv aislado
# Etapa 2: runner   → imagen mínima de producción, usuario no-root
# =============================================================================

# ── Etapa 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema necesarias para compilar psycopg y Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear y activar virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias de producción primero (layer cacheado si no cambian)
COPY requirements/base.txt requirements/production.txt ./requirements/
RUN pip install --upgrade pip && \
    pip install -r requirements/production.txt

# ── Etapa 2: Runner ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PORT=8000

# Solo librerías de runtime (sin build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Copiar virtualenv desde builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Usuario no-root (seguridad)
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /bin/false appuser

# Copiar código fuente
COPY --chown=appuser:appgroup . .

# Entrypoint y permisos
COPY --chown=appuser:appgroup docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Directorios de archivos estáticos/media con permisos correctos
RUN mkdir -p /app/staticfiles /app/mediafiles && \
    chown -R appuser:appgroup /app/staticfiles /app/mediafiles

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn"]
