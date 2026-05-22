#!/bin/bash
# =============================================================================
# ChickenFifa — Script de despliegue completo en OCI (Ubuntu 22.04 LTS)
#
# Qué hace este script:
#   1. Actualiza el sistema e instala dependencias del servidor
#   2. Instala Docker + Docker Compose plugin
#   3. Instala Nginx
#   4. Configura DuckDNS (actualización automática de IP)
#   5. Obtiene certificado SSL con Certbot + Let's Encrypt
#   6. Configura Nginx como reverse proxy con HTTPS
#   7. Prepara el directorio de la aplicación
#   8. Crea el archivo .env de producción de forma interactiva
#   9. Levanta la aplicación con Docker Compose
#
# USO:
#   scp scripts/deploy_oci.sh ubuntu@TU_IP_OCI:/tmp/
#   ssh ubuntu@TU_IP_OCI "bash /tmp/deploy_oci.sh"
#
# PRERREQUISITOS:
#   - Instancia OCI con Ubuntu 22.04 LTS
#   - Cuenta DuckDNS con subdominio creado (https://www.duckdns.org)
#   - Puerto 80, 443 y 22 abiertos en el Security List de OCI
#   - Registros DNS de DuckDNS apuntando a la IP pública del servidor
# =============================================================================

set -euo pipefail

# ── Colores para output ───────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

log()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()   { echo -e "${YELLOW}[!]${NC} $1"; }
info()   { echo -e "${BLUE}[→]${NC} $1"; }
header() { echo -e "\n${CYAN}${BOLD}══════════════════════════════════════════${NC}"; echo -e "${CYAN}${BOLD}  $1${NC}"; echo -e "${CYAN}${BOLD}══════════════════════════════════════════${NC}\n"; }
error()  { echo -e "${RED}[✗] ERROR: $1${NC}" >&2; exit 1; }

# ── Verificación inicial ──────────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ] && ! groups | grep -q "\bsudo\b"; then
    error "Este script requiere permisos sudo. Ejecútalo con: sudo bash deploy_oci.sh"
fi

SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

header "ChickenFifa — Deploy Automático en OCI"

# ── Recolección de parámetros ─────────────────────────────────────────────────
echo -e "${BOLD}Configuración requerida:${NC}"
echo ""

read -rp "$(echo -e "${CYAN}Tu subdominio DuckDNS${NC} (sin .duckdns.org, ej: chickenfifa): ")" DUCKDNS_SUBDOMAIN
read -rp "$(echo -e "${CYAN}Token de DuckDNS${NC} (desde https://www.duckdns.org): ")" DUCKDNS_TOKEN
read -rp "$(echo -e "${CYAN}Email para Let's Encrypt${NC} (para notificaciones de expiración): ")" LETSENCRYPT_EMAIL

DOMAIN="${DUCKDNS_SUBDOMAIN}.duckdns.org"
APP_DIR="/opt/chickenfifa"

echo ""
echo -e "${BOLD}Parámetros de producción Django:${NC}"
read -rp "$(echo -e "${CYAN}SECRET_KEY Django${NC} (vacío = auto-generada): ")" DJANGO_SECRET_KEY
read -rp "$(echo -e "${CYAN}Password para PostgreSQL${NC}: ")" DB_PASSWORD
read -rsp "$(echo -e "${CYAN}Password para superusuario Django${NC}: ")" DJANGO_SUPER_PASS
echo ""
read -rp "$(echo -e "${CYAN}Email del superusuario Django${NC}: ")" DJANGO_SUPER_EMAIL

# Generar SECRET_KEY si no se proporcionó
if [ -z "$DJANGO_SECRET_KEY" ]; then
    DJANGO_SECRET_KEY=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#\$%^&*(-_=+)') for _ in range(64)))")
    log "SECRET_KEY generada automáticamente."
fi

echo ""
read -rp "$(echo -e "${CYAN}URL del repositorio GitHub${NC} (ej: https://github.com/diegofretes96/chickenfifa.git): ")" GITHUB_REPO_URL

# OCI Registry (opcional si no se usa CI/CD todavía)
read -rp "$(echo -e "${CYAN}OCI Registry${NC} (vacío para usar build local): ")" OCI_REGISTRY
USE_OCI_REGISTRY=false
[ -n "$OCI_REGISTRY" ] && USE_OCI_REGISTRY=true

echo ""
warn "Resumen de configuración:"
echo "  Dominio:    ${DOMAIN}"
echo "  App dir:    ${APP_DIR}"
echo "  Repo:       ${GITHUB_REPO_URL}"
echo ""
read -rp "¿Continuar? [s/N]: " CONFIRM
[[ "$CONFIRM" =~ ^[sS]$ ]] || error "Deploy cancelado por el usuario."

# =============================================================================
# PASO 1: Actualizar sistema
# =============================================================================
header "PASO 1/9 — Actualización del sistema"

$SUDO apt-get update -qq
$SUDO apt-get upgrade -y -qq
$SUDO apt-get install -y -qq \
    curl \
    wget \
    git \
    unzip \
    jq \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    ufw \
    fail2ban \
    htop \
    logrotate \
    cron

log "Sistema actualizado."

# =============================================================================
# PASO 2: Instalar Docker + Docker Compose
# =============================================================================
header "PASO 2/9 — Instalación de Docker"

if command -v docker &>/dev/null; then
    warn "Docker ya está instalado ($(docker --version)). Omitiendo."
else
    info "Instalando Docker Engine..."

    # Agregar clave GPG oficial de Docker
    $SUDO install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    $SUDO chmod a+r /etc/apt/keyrings/docker.gpg

    # Agregar repositorio Docker
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | \
        $SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null

    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

    # Agregar usuario actual al grupo docker
    $SUDO usermod -aG docker "${USER:-ubuntu}"

    log "Docker $(docker --version) instalado."
fi

# Habilitar y arrancar Docker
$SUDO systemctl enable docker
$SUDO systemctl start docker

# Verificar docker compose plugin
docker compose version &>/dev/null || error "docker compose plugin no disponible."
log "Docker Compose plugin disponible."

# =============================================================================
# PASO 3: Instalar y configurar Nginx
# =============================================================================
header "PASO 3/9 — Instalación de Nginx"

if command -v nginx &>/dev/null; then
    warn "Nginx ya está instalado. Omitiendo instalación."
else
    $SUDO apt-get install -y -qq nginx
    log "Nginx instalado."
fi

$SUDO systemctl enable nginx
$SUDO systemctl start nginx
log "Nginx activo."

# =============================================================================
# PASO 4: Configurar Firewall (UFW)
# =============================================================================
header "PASO 4/9 — Configuración del Firewall"

$SUDO ufw --force reset > /dev/null
$SUDO ufw default deny incoming
$SUDO ufw default allow outgoing
$SUDO ufw allow 22/tcp comment 'SSH'
$SUDO ufw allow 80/tcp comment 'HTTP'
$SUDO ufw allow 443/tcp comment 'HTTPS'
$SUDO ufw --force enable

log "Firewall configurado (22, 80, 443)."

# =============================================================================
# PASO 5: Configurar DuckDNS
# =============================================================================
header "PASO 5/9 — Configuración de DuckDNS"

DUCKDNS_DIR="/opt/duckdns"
$SUDO mkdir -p "$DUCKDNS_DIR"

# Script de actualización de IP
$SUDO tee "${DUCKDNS_DIR}/duck.sh" > /dev/null << DUCKEOF
#!/bin/bash
# Actualiza la IP pública en DuckDNS
RESULT=\$(curl -s "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=")
echo "\$(date) — \$RESULT" >> /var/log/duckdns.log
DUCKEOF

$SUDO chmod +x "${DUCKDNS_DIR}/duck.sh"

# Cronjob cada 5 minutos
CRON_JOB="*/5 * * * * /opt/duckdns/duck.sh >/dev/null 2>&1"
( crontab -l 2>/dev/null | grep -v "duckdns" ; echo "$CRON_JOB" ) | crontab -

# Ejecutar una vez ahora para actualizar la IP inmediatamente
bash "${DUCKDNS_DIR}/duck.sh"
log "DuckDNS configurado para ${DOMAIN} (actualización cada 5 min)."
info "Espera 30 segundos para que DNS propague antes de obtener el certificado..."
sleep 30

# =============================================================================
# PASO 6: Obtener certificado SSL con Certbot
# =============================================================================
header "PASO 6/9 — Certificado SSL con Let's Encrypt"

# Instalar Certbot via snap (método recomendado por EFF)
if ! command -v certbot &>/dev/null; then
    $SUDO snap install --classic certbot
    $SUDO ln -sf /snap/bin/certbot /usr/bin/certbot
    log "Certbot instalado."
else
    warn "Certbot ya instalado. Omitiendo."
fi

# Configuración Nginx temporal para que Certbot pueda hacer el challenge HTTP-01
$SUDO tee /etc/nginx/sites-available/chickenfifa-temp > /dev/null << NGINXEOF
server {
    listen 80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'Aguarda...';
        add_header Content-Type text/plain;
    }
}
NGINXEOF

$SUDO mkdir -p /var/www/certbot
$SUDO ln -sf /etc/nginx/sites-available/chickenfifa-temp /etc/nginx/sites-enabled/chickenfifa-temp
$SUDO rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
$SUDO nginx -t && $SUDO systemctl reload nginx

log "Nginx temporal configurado para challenge HTTP."

# Obtener certificado
$SUDO certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$LETSENCRYPT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d "$DOMAIN" \
    && log "Certificado SSL obtenido para ${DOMAIN}." \
    || error "No se pudo obtener el certificado. Verifica que ${DOMAIN} apunte a la IP correcta."

# Renovación automática (cronjob de Certbot)
echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'" | \
    $SUDO tee /etc/cron.d/certbot-renew > /dev/null
log "Renovación automática de certificado configurada (diaria a las 3am)."

# Eliminar config temporal
$SUDO rm /etc/nginx/sites-enabled/chickenfifa-temp

# =============================================================================
# PASO 7: Configurar Nginx para producción con HTTPS
# =============================================================================
header "PASO 7/9 — Configuración Nginx de producción"

$SUDO tee /etc/nginx/sites-available/chickenfifa > /dev/null << NGINXPROD
# ── ChickenFifa — Nginx producción con HTTPS ──────────────────────────────────

# Redirigir todo HTTP → HTTPS
server {
    listen 80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS — Proxy a Gunicorn
server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    # Certificados Let's Encrypt
    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # Configuración SSL robusta
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_stapling        on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    client_max_body_size 10M;

    # Archivos estáticos (servidos por Nginx, sin tocar Django)
    location /static/ {
        alias /opt/chickenfifa/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Archivos de media
    location /media/ {
        alias /opt/chickenfifa/mediafiles/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Certbot challenge renewal
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Todo lo demás → Gunicorn en Docker
    location / {
        proxy_pass          http://127.0.0.1:8000;
        proxy_http_version  1.1;
        proxy_set_header    Host              \$host;
        proxy_set_header    X-Real-IP         \$remote_addr;
        proxy_set_header    X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto \$scheme;
        proxy_set_header    Upgrade           \$http_upgrade;
        proxy_set_header    Connection        "upgrade";
        proxy_connect_timeout 30s;
        proxy_read_timeout    120s;
        proxy_send_timeout    120s;
    }
}
NGINXPROD

$SUDO ln -sf /etc/nginx/sites-available/chickenfifa /etc/nginx/sites-enabled/chickenfifa
$SUDO nginx -t || error "Configuración de Nginx inválida."
$SUDO systemctl reload nginx
log "Nginx configurado con HTTPS para ${DOMAIN}."

# =============================================================================
# PASO 8: Preparar directorio de la aplicación
# =============================================================================
header "PASO 8/9 — Preparación de la aplicación"

# Clonar o actualizar repositorio
if [ -d "$APP_DIR/.git" ]; then
    info "Repositorio ya existe. Actualizando..."
    cd "$APP_DIR" && git pull origin main
else
    info "Clonando repositorio..."
    $SUDO git clone "$GITHUB_REPO_URL" "$APP_DIR"
    $SUDO chown -R "${USER:-ubuntu}:${USER:-ubuntu}" "$APP_DIR"
fi

cd "$APP_DIR"
log "Código fuente en ${APP_DIR}."

# Crear directorios de archivos
mkdir -p "${APP_DIR}/staticfiles" "${APP_DIR}/mediafiles"

# Crear archivo .env de producción
info "Creando archivo .env de producción..."
cat > "${APP_DIR}/.env" << ENVEOF
# =====================================================
# ChickenFifa — Variables de producción
# Generado automáticamente por deploy_oci.sh
# NUNCA commitear este archivo al repositorio
# =====================================================

# Django
SECRET_KEY=${DJANGO_SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN},www.${DOMAIN}
DJANGO_SETTINGS_MODULE=config.settings.production

# Base de datos
DATABASE_URL=postgres://chickenfifa:${DB_PASSWORD}@db:5432/chickenfifa_db
CONN_MAX_AGE=60

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/0

# Torneo
PREDICTION_LOCK_MINUTES=30

# Superusuario automático (primer deploy)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPER_EMAIL}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPER_PASS}

# Gunicorn
GUNICORN_WORKERS=3
GUNICORN_LOG_LEVEL=info
PORT=8000

# Celery
CELERY_LOG_LEVEL=info
CELERY_CONCURRENCY=2

# Sentry (opcional — agrega el DSN si lo usas)
SENTRY_DSN=
ENVEOF

chmod 600 "${APP_DIR}/.env"
log "Archivo .env creado con permisos restrictivos (600)."

# docker-compose.prod necesita las variables de imagen OCI
# Si no se usa OCI Registry, usar build local
if [ "$USE_OCI_REGISTRY" = false ]; then
    info "Usando build local (sin OCI Registry)..."
    # Sobrescribir docker-compose.prod.yml para build local
    cat > "${APP_DIR}/docker-compose.local-prod.yml" << LOCALPROD
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: chickenfifa_db
      POSTGRES_USER: chickenfifa
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chickenfifa -d chickenfifa_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  web:
    build:
      context: .
      dockerfile: Dockerfile
      target: runner
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
    command: gunicorn
    volumes:
      - ${APP_DIR}/staticfiles:/app/staticfiles
      - ${APP_DIR}/mediafiles:/app/mediafiles
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always

  celery:
    build:
      context: .
      dockerfile: Dockerfile
      target: runner
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
    command: celery
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always

volumes:
  postgres_data:
LOCALPROD
    COMPOSE_FILE="docker-compose.local-prod.yml"
else
    COMPOSE_FILE="docker-compose.prod.yml"
fi

# =============================================================================
# PASO 9: Arrancar la aplicación
# =============================================================================
header "PASO 9/9 — Arranque de la aplicación"

cd "$APP_DIR"

info "Construyendo imagen Docker..."
docker compose -f "$COMPOSE_FILE" build --no-cache

info "Iniciando servicios..."
docker compose -f "$COMPOSE_FILE" up -d

info "Esperando que los servicios estén saludables..."
sleep 20

# Verificar estado
if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    log "Servicios Docker corriendo."
else
    warn "Algunos servicios pueden no estar listos. Verificar con: docker compose ps"
fi

# Crear servicio systemd para auto-arranque
info "Configurando inicio automático..."
$SUDO tee /etc/systemd/system/chickenfifa.service > /dev/null << SYSTEMD
[Unit]
Description=ChickenFifa — Polla Mundial FIFA 2026
After=docker.service network.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/docker compose -f ${COMPOSE_FILE} up -d
ExecStop=/usr/bin/docker compose -f ${COMPOSE_FILE} down
TimeoutStartSec=300
User=${USER:-ubuntu}

[Install]
WantedBy=multi-user.target
SYSTEMD

$SUDO systemctl daemon-reload
$SUDO systemctl enable chickenfifa
log "Servicio systemd configurado (inicio automático tras reboot)."

# Configurar logrotate para logs de Docker
$SUDO tee /etc/logrotate.d/chickenfifa > /dev/null << LOGROTATE
/var/log/duckdns.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
LOGROTATE

# =============================================================================
# RESUMEN FINAL
# =============================================================================
header "✅ Deploy completado"

PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "No disponible")

echo -e "${GREEN}${BOLD}La aplicación ChickenFifa está corriendo en:${NC}"
echo ""
echo -e "  ${CYAN}🌐 URL:${NC}     https://${DOMAIN}"
echo -e "  ${CYAN}🔒 HTTPS:${NC}   Certificado Let's Encrypt activo"
echo -e "  ${CYAN}🖥️  IP OCI:${NC}  ${PUBLIC_IP}"
echo -e "  ${CYAN}📁 Dir:${NC}     ${APP_DIR}"
echo ""
echo -e "${YELLOW}${BOLD}Próximos pasos:${NC}"
echo ""
echo "  1. Admin de Django:"
echo "     https://${DOMAIN}/admin/"
echo "     Usuario: admin | Password: (el que ingresaste)"
echo ""
echo "  2. Verificar logs:"
echo "     docker compose -f ${APP_DIR}/${COMPOSE_FILE} logs -f web"
echo ""
echo "  3. Para actualizaciones manuales:"
echo "     cd ${APP_DIR} && git pull && docker compose -f ${COMPOSE_FILE} up -d --build"
echo ""
echo "  4. Cargar fixture de equipos FIFA 2026:"
echo "     docker compose -f ${APP_DIR}/${COMPOSE_FILE} exec web python manage.py loaddata fixtures/equipos_fifa2026.json"
echo ""
echo "  5. DuckDNS se actualiza automáticamente cada 5 min."
echo "     Logs: tail -f /var/log/duckdns.log"
echo ""
echo -e "${GREEN}${BOLD}GitHub Secrets para CI/CD automático:${NC}"
echo ""
echo "  OCI_INSTANCE_IP       = ${PUBLIC_IP}"
echo "  OCI_SSH_PRIVATE_KEY   = (contenido de tu ~/.ssh/id_rsa privada)"
echo ""
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo -e "${CYAN} ChickenFifa desplegado exitosamente 🐔⚽${NC}"
echo -e "${CYAN}══════════════════════════════════════════${NC}"
