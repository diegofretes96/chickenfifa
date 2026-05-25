# 🐔 ChickenFifa — Polla del Mundial FIFA 2026

> Aplicación web de quiniela/polla para el **FIFA World Cup 2026** (formato 48 equipos).  
> Construida con Django 5.x · PostgreSQL · Docker · Celery · desplegada en Oracle Cloud Infrastructure.

---

## Características principales

| Módulo | Descripción |
|---|---|
| **Pronósticos** | Predice el marcador de los 104 partidos (grupos + eliminatorias) |
| **Cierre automático** | Los pronósticos se bloquean N minutos antes de cada partido |
| **Sistema de puntos** | Exacto: 5 pts · Resultado correcto: 3 pts · Equipo clasifica: 2 pts |
| **Bracket dinámico** | El cuadro eliminatorio se genera automáticamente al avanzar rondas |
| **Grupos privados** | Crea tu grupo con un código de invitación único |
| **Tabla en vivo** | Clasificación global y por grupo privado con tendencia (↑↓=) |
| **Admin potenciado** | Registra resultados oficiales → recálculo asíncrono de puntos vía Celery |
| **Banderas de países** | Iconos de bandera via `flag-icons` CSS para los 48 equipos participantes |

---

## Stack tecnológico

```
Backend     Django 5.1 · Python 3.12 · Django REST (templates + HTMX)
Base datos  PostgreSQL 16
Cache/Queue Redis 7 · Celery 5
Servidor    Gunicorn · Nginx · Let's Encrypt (HTTPS)
Infra       Docker (multi-stage) · Docker Compose
CI/CD       GitHub Actions → OCIR (Oracle Container Registry) → OCI Compute
DNS         DuckDNS (dominio gratuito)
UI          Bootstrap 5.3 · Bootstrap Icons · flag-icons 7.2
```

---

## Formato FIFA 2026

```
48 equipos · 12 grupos (A–L) · 4 equipos por grupo
─────────────────────────────────────────────────
Fase de Grupos      72 partidos   (6 por grupo × 12)
Dieciseisavos       16 partidos   (Top 2 × 12 grupos + 8 mejores 3°)
Octavos de Final     8 partidos
Cuartos de Final     4 partidos
Semifinales          2 partidos
Tercer Puesto        1 partido
Final                1 partido
─────────────────────────────────────────────────
TOTAL              104 partidos
```

---

## Changelog

### v1.1.0 — 2026-05-25

- **UI pronósticos rediseñada**: nueva vista de fase de grupos con panel lateral de navegación por grupo y tarjetas horizontales de partido (inspirado en F5 LATAM Cup).
- **Banderas de países**: integración de `flag-icons` CSS — cada equipo muestra su bandera nacional. Mapeo FIFA 3 letras → ISO 3166-1 alpha-2 para todos los grupos confederados (CONCACAF, CONMEBOL, UEFA, CAF, AFC, OFC).
- **Corrección marcador 0 goles**: el filtro `|default:''` trataba `0` como valor nulo y dejaba el campo vacío. Corregido con `|default_if_none:''` para mostrar correctamente el 0.
- **Registro simplificado**: el formulario de registro ahora solo requiere nombre de usuario y contraseña — se eliminó el campo de correo electrónico que no tenía uso funcional.

---

## Inicio rápido (desarrollo local)

### Prerrequisitos

- Docker Desktop ≥ 24
- Python 3.12 (para desarrollo sin Docker)
- Git

### 1. Clonar y configurar entorno

```bash
git clone https://github.com/diegofretes96/chickenfifa.git
cd chickenfifa

# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus valores (mínimo SECRET_KEY)
```

### 2. Levantar con Docker Compose

```bash
# Construir e iniciar todos los servicios
docker compose up --build -d

# Ver logs
docker compose logs -f web

# Crear superusuario
docker compose exec web python manage.py createsuperuser

# Cargar datos iniciales (equipos FIFA 2026)
docker compose exec web python manage.py loaddata fixtures/equipos_fifa2026.json
```

La aplicación queda disponible en **http://localhost:8000**  
El admin en **http://localhost:8000/admin/**

### 3. Desarrollo sin Docker

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements/local.txt

# Base de datos PostgreSQL local corriendo
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Celery worker (segunda terminal)
celery -A config worker --loglevel=info
```

---

## Variables de entorno

Todas las variables se cargan desde `.env` via `django-environ`.  
Ver [.env.example](.env.example) para la lista completa.

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta Django | `django-insecure-...` |
| `DATABASE_URL` | URL PostgreSQL | `postgres://user:pass@db:5432/dbname` |
| `CELERY_BROKER_URL` | URL Redis | `redis://redis:6379/0` |
| `PREDICTION_LOCK_MINUTES` | Minutos de cierre antes del partido | `30` |
| `DEBUG` | Modo debug | `False` en producción |
| `ALLOWED_HOSTS` | Hosts permitidos | `chickenfifa.duckdns.org` |

---

## Sistema de puntos

```
┌─────────────────────────────────────────────┬────────┐
│ Pronóstico                                  │ Puntos │
├─────────────────────────────────────────────┼────────┤
│ Resultado exacto (ej: 2-1 real → 2-1 pred) │   5    │
│ Resultado correcto (ej: 2-1 real → 3-0 pred)│   3    │
│ Equipo clasificó a siguiente fase           │   2    │
└─────────────────────────────────────────────┴────────┘
```

---

## Despliegue en producción (OCI + DuckDNS)

Ver el script completo de instalación en [`scripts/deploy_oci.sh`](scripts/deploy_oci.sh).

### Resumen del proceso

```
1. Crear Compute Instance en OCI (Ubuntu 22.04)
2. Apuntar dominio DuckDNS a la IP pública del servidor
3. Ejecutar: bash scripts/deploy_oci.sh
4. Configurar GitHub Secrets (ver sección CI/CD)
5. Push a main → deploy automático
```

### GitHub Secrets requeridos para CI/CD

| Secret | Descripción |
|---|---|
| `OCI_REGISTRY` | `<region>.ocir.io` |
| `OCI_NAMESPACE` | Namespace de tu tenancy OCI |
| `OCI_USERNAME` | Usuario OCI |
| `OCI_AUTH_TOKEN` | Auth Token generado en OCI Console |
| `OCI_REPO_NAME` | `chickenfifa` |
| `OCI_INSTANCE_IP` | IP pública del servidor |
| `OCI_SSH_PRIVATE_KEY` | Clave privada SSH (contenido completo) |

---

## Estructura del proyecto

```
chickenfifa/
├── .github/workflows/deploy.yml    # CI/CD: test → build → deploy
├── apps/
│   ├── accounts/                   # PerfilUsuario, GrupoPolla
│   ├── tournament/                 # Equipo, Partido (104 matches)
│   ├── predictions/                # Pronostico, scoring engine, Celery tasks
│   └── leaderboard/                # SnapshotClasificacion
├── config/
│   ├── settings/{base,local,production}.py
│   └── celery.py
├── templates/                      # HTML en español (Bootstrap 5 + HTMX)
├── static/
├── scripts/
│   └── deploy_oci.sh               # Script completo de deploy en servidor
├── docker/
│   ├── entrypoint.sh
│   └── nginx/nginx.conf
├── Dockerfile                      # Multi-stage (builder + runner no-root)
├── docker-compose.yml              # Desarrollo local
└── docker-compose.prod.yml         # Producción
```

---

## Contribuir

```bash
# Crear rama
git checkout -b feature/mi-feature

# Lint y tests antes de commit
ruff check .
pytest

# Pull request a main
```

---

## Licencia

MIT © 2025 — [diegofretes96](https://github.com/diegofretes96)
