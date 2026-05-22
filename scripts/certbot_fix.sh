#!/bin/bash
# =============================================================================
# certbot_fix.sh — Obtener certificado SSL en OCI cuando webroot falla
#
# Causa del error: OCI tiene DOS capas de firewall:
#   1. OCI Security List (red VCN) — DEBE estar abierto en la consola OCI
#   2. iptables del OS — las imágenes Ubuntu de OCI traen una regla REJECT
#      al final que bloquea tráfico aunque UFW diga que está abierto.
#
# Este script:
#   1. Muestra diagnóstico completo de conectividad
#   2. Limpia las reglas iptables problemáticas de OCI
#   3. Usa modo --standalone (para nginx, pide cert, reactiva nginx)
#   4. Reconfigura nginx con el certificado obtenido
#
# USO:
#   sudo bash scripts/certbot_fix.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()   { echo -e "${YELLOW}[!]${NC} $1"; }
info()   { echo -e "${BLUE}[→]${NC} $1"; }
error()  { echo -e "${RED}[✗] ERROR:${NC} $1" >&2; exit 1; }
header() { echo -e "\n${CYAN}${BOLD}══ $1 ══${NC}\n"; }

[ "$(id -u)" -ne 0 ] && error "Ejecutar con sudo: sudo bash certbot_fix.sh"

# ── Pedir datos ───────────────────────────────────────────────────────────────
header "Datos requeridos"
read -rp "Subdominio DuckDNS (ej: chickenmundial): " DUCKDNS_SUBDOMAIN
read -rp "Token DuckDNS: " DUCKDNS_TOKEN
read -rp "Email para Let's Encrypt: " LETSENCRYPT_EMAIL

DOMAIN="${DUCKDNS_SUBDOMAIN}.duckdns.org"
PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "desconocida")

# ── PASO 1: Diagnóstico ───────────────────────────────────────────────────────
header "PASO 1 — Diagnóstico de conectividad"

info "IP pública del servidor: ${PUBLIC_IP}"

# Verificar resolución DNS del dominio
DNS_IP=$(dig +short "$DOMAIN" 2>/dev/null || nslookup "$DOMAIN" 2>/dev/null | grep "Address:" | tail -1 | awk '{print $2}' || echo "no_resuelve")
info "IP que resuelve ${DOMAIN}: ${DNS_IP}"

if [ "$DNS_IP" != "$PUBLIC_IP" ]; then
    warn "¡ATENCIÓN! El dominio no apunta a este servidor."
    warn "  Dominio resuelve a: ${DNS_IP}"
    warn "  IP de este servidor: ${PUBLIC_IP}"
    warn "Actualizando DuckDNS ahora..."
    DUCK_RESP=$(curl -s "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=" || true)
    if [ "$DUCK_RESP" = "OK" ]; then
        log "DuckDNS actualizado. Esperando 30s para propagación..."
        sleep 30
    else
        error "DuckDNS respondió: '${DUCK_RESP}'. Verifica el subdominio y el token."
    fi
else
    log "DNS correcto: ${DOMAIN} → ${PUBLIC_IP}"
fi

# Verificar estado de iptables
info "Reglas iptables INPUT actuales:"
iptables -L INPUT --line-numbers -n 2>/dev/null | head -20 || true

# Verificar UFW
info "Estado UFW:"
ufw status numbered 2>/dev/null | head -20 || true

# ── PASO 2: Limpiar reglas iptables problemáticas de OCI ─────────────────────
header "PASO 2 — Limpieza de iptables (reglas REJECT de OCI)"

info "Las imágenes Ubuntu de OCI incluyen reglas REJECT que bloquean puertos"
info "aunque UFW esté configurado para permitirlos."

# Eliminar reglas REJECT que OCI agrega por defecto
iptables -D INPUT  -j REJECT --reject-with icmp-host-prohibited 2>/dev/null && \
    log "Eliminada regla REJECT en INPUT." || \
    warn "No había regla REJECT en INPUT (o ya fue eliminada)."

iptables -D FORWARD -j REJECT --reject-with icmp-host-prohibited 2>/dev/null && \
    log "Eliminada regla REJECT en FORWARD." || \
    warn "No había regla REJECT en FORWARD."

# Verificar que los puertos están abiertos a nivel OS
if iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null; then
    log "Puerto 80 permitido en iptables."
else
    iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
    log "Regla ACCEPT para puerto 80 agregada."
fi

if iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null; then
    log "Puerto 443 permitido en iptables."
else
    iptables -I INPUT 2 -p tcp --dport 443 -j ACCEPT
    log "Regla ACCEPT para puerto 443 agregada."
fi

# Guardar reglas para que persistan tras reboot
if command -v netfilter-persistent &>/dev/null; then
    netfilter-persistent save
elif command -v iptables-save &>/dev/null; then
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
fi

# ── PASO 3: Verificar acceso desde internet ───────────────────────────────────
header "PASO 3 — Verificación de acceso externo"

warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warn "ACCIÓN MANUAL REQUERIDA EN OCI CONSOLE (si aún no lo hiciste):"
warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Ir a: https://cloud.oracle.com → Networking → Virtual Cloud Networks"
echo "  2. Clic en tu VCN → Security Lists → Default Security List"
echo "  3. Add Ingress Rules:"
echo ""
echo "     ┌──────────────────────────────────────────────────────┐"
echo "     │  Source CIDR:  0.0.0.0/0                            │"
echo "     │  Protocol:     TCP                                   │"
echo "     │  Dest Port:    80    (HTTP — para Certbot)          │"
echo "     └──────────────────────────────────────────────────────┘"
echo "     ┌──────────────────────────────────────────────────────┐"
echo "     │  Source CIDR:  0.0.0.0/0                            │"
echo "     │  Protocol:     TCP                                   │"
echo "     │  Dest Port:    443   (HTTPS)                        │"
echo "     └──────────────────────────────────────────────────────┘"
echo ""

read -rp "¿Ya abriste los puertos 80 y 443 en OCI Console? [s/N]: " CONFIRM_OCI
[[ "$CONFIRM_OCI" =~ ^[sS]$ ]] || {
    warn "Abre los puertos en OCI Console primero y vuelve a ejecutar este script."
    exit 0
}

# Test de conectividad al puerto 80 desde afuera (usando servicio externo)
info "Probando acceso al puerto 80 desde internet..."
nginx -t 2>/dev/null && systemctl reload nginx || true

# Levantar servidor de prueba temporal
python3 -m http.server 80 --directory /var/www/certbot &
HTTP_PID=$!
sleep 2

ACME_TEST_DIR="/var/www/certbot/.well-known/acme-challenge"
mkdir -p "$ACME_TEST_DIR"
echo "test-ok" > "${ACME_TEST_DIR}/test"

# Probar acceso desde internet usando api externa
HTTP_TEST=$(curl -s --max-time 10 \
    "https://api.github.com/markdown" 2>/dev/null \
    || echo "no_connection")

# Test directo al propio dominio
DOMAIN_TEST=$(curl -s --max-time 8 \
    "http://${DOMAIN}/.well-known/acme-challenge/test" 2>/dev/null || echo "")

kill $HTTP_PID 2>/dev/null || true
rm -f "${ACME_TEST_DIR}/test"

if [ "$DOMAIN_TEST" = "test-ok" ]; then
    log "Puerto 80 accesible desde internet. Procediendo con Certbot."
else
    warn "No se pudo verificar acceso externo al puerto 80."
    warn "Posibles causas:"
    warn "  • OCI Security List sin abrir (revisar Ingress Rules)"
    warn "  • Nginx bloqueando la ruta /.well-known/"
    warn "Continuando de todas formas con modo standalone..."
fi

# ── PASO 4: Obtener certificado (modo standalone) ─────────────────────────────
header "PASO 4 — Obtener certificado SSL con Certbot (modo standalone)"

info "Modo standalone: detiene Nginx temporalmente, usa su propio servidor HTTP"
info "para el challenge, luego Nginx se reactiva con el certificado."

# Detener Nginx para que certbot pueda usar el puerto 80
systemctl stop nginx
log "Nginx detenido temporalmente."

# Obtener certificado
if certbot certonly \
    --standalone \
    --preferred-challenges http \
    --email "$LETSENCRYPT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --force-renewal \
    -d "$DOMAIN"; then
    log "¡Certificado SSL obtenido exitosamente!"
    CERT_OK=true
else
    warn "Certbot standalone también falló. Intentando modo DNS manual..."
    CERT_OK=false
fi

# Reactivar Nginx siempre, haya o no certificado
systemctl start nginx
log "Nginx reactivado."

if [ "$CERT_OK" = false ]; then
    header "ALTERNATIVA — Certificado DNS (no requiere puerto 80)"
    echo ""
    warn "El método HTTP falló. Usa el método DNS manual:"
    echo ""
    echo "  sudo certbot certonly \\"
    echo "    --manual \\"
    echo "    --preferred-challenges dns \\"
    echo "    --email ${LETSENCRYPT_EMAIL} \\"
    echo "    --agree-tos \\"
    echo "    -d ${DOMAIN}"
    echo ""
    echo "  Certbot te pedirá que agregues un registro TXT en DuckDNS:"
    echo "  Ve a https://www.duckdns.org y agrega el TXT record que te indique."
    echo ""
    exit 1
fi

# ── PASO 5: Reconfigurar Nginx con el certificado ─────────────────────────────
header "PASO 5 — Configurar Nginx con HTTPS"

NGINX_CONF="/etc/nginx/sites-available/chickenfifa"

# Verificar que el archivo de Nginx existe (instalado por deploy_oci.sh)
if [ ! -f "$NGINX_CONF" ]; then
    warn "Config de Nginx no encontrada en ${NGINX_CONF}."
    warn "Creando configuración básica..."

    cat > "$NGINX_CONF" << NGINXEOF
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://\$host\$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;

    client_max_body_size 10M;

    location /static/  { alias /opt/chickenfifa/staticfiles/; expires 30d; }
    location /media/   { alias /opt/chickenfifa/mediafiles/; expires 7d; }
    location /.well-known/acme-challenge/ { root /var/www/certbot; }

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
NGINXEOF
    ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/chickenfifa
fi

nginx -t || error "Configuración de Nginx inválida."
systemctl reload nginx
log "Nginx recargado con certificado SSL."

# ── Renovación automática ──────────────────────────────────────────────────────
echo "0 3 * * * root certbot renew --quiet --post-hook 'systemctl reload nginx'" \
    > /etc/cron.d/certbot-renew
log "Renovación automática configurada (3am diario)."

# ── Persistir reglas iptables ─────────────────────────────────────────────────
apt-get install -y -qq iptables-persistent 2>/dev/null || true
netfilter-persistent save 2>/dev/null || iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
log "Reglas iptables guardadas para persistir tras reboot."

# ── Resumen ───────────────────────────────────────────────────────────────────
header "✅ Certificado SSL instalado"
echo ""
echo -e "  ${GREEN}${BOLD}https://${DOMAIN}${NC}"
echo ""
echo "  Certificado: /etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
echo "  Expira en:   90 días (renovación automática activa)"
echo ""
echo "  Próximo paso: verificar la app"
echo "  curl -I https://${DOMAIN}"
echo ""
