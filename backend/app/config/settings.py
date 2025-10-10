from dotenv import load_dotenv
import os
from typing import List
from pathlib import Path

# Carga .env desde la raíz del backend aunque el cwd sea distinto (mod_wsgi)
_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[2]  # backend/

# Cargar variables desde .env si existe (local dev). En Docker, .dockerignore evita copiarlo.
_ENV_FILE = _BACKEND_ROOT / ".env"
if _ENV_FILE.exists():
	load_dotenv(dotenv_path=_ENV_FILE)


def _list_from_env(var_name: str, default: str = "") -> List[str]:
	raw = os.getenv(var_name, default) or ""
	items = [x.strip() for x in raw.split(",") if x.strip()]
	return items


# --- App settings ---
APP_NAME: str = os.getenv("APP_NAME", "HSOMarine API")
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes", "on")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
ROOT_PATH: str = os.getenv("ROOT_PATH", "")

# CORS y seguridad
# Por defecto permitimos localhost:3000 y 127.0.0.1:3000 (Next.js) en desarrollo si no se define CORS_ORIGINS
CORS_ORIGINS: List[str] = _list_from_env("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_HOSTS: List[str] = _list_from_env("ALLOWED_HOSTS", "")

# Documentación sólo visible en DEBUG
DOCS_URL = "/docs" if DEBUG else None
REDOC_URL = "/redoc" if DEBUG else None
OPENAPI_URL = "/openapi.json" if DEBUG else None


# --- Odoo credentials ---
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")
ODOO_TIMEOUT = int(os.getenv("ODOO_TIMEOUT", 30))  # Timeout por defecto para Odoo (en segundos)
# Reintentos y backoff para llamadas Odoo (XML-RPC)
ODOO_MAX_RETRIES = int(os.getenv("ODOO_MAX_RETRIES", "3"))
ODOO_RETRY_BACKOFF = float(os.getenv("ODOO_RETRY_BACKOFF", "0.35"))  # segundos (exponencial)

# Odoo STAGING (opcional, para segundo entorno)
ODOO_STAGING_URL: str | None = os.getenv("ODOO_STAGING_URL")
ODOO_STAGING_DB: str | None = os.getenv("ODOO_STAGING_DB")
ODOO_STAGING_USER: str | None = os.getenv("ODOO_STAGING_USER")
ODOO_STAGING_PASSWORD: str | None = os.getenv("ODOO_STAGING_PASSWORD")

# --- Cache / Redis (opcional) ---
# Redis para cache compartida entre workers (si se configura)
REDIS_URL: str | None = os.getenv("REDIS_URL")

# --- Base de Datos: Postgres (producción / local) ---
DB_PROFILE = os.getenv("DB_PROFILE", "prod").lower()  # prod | local

# Valores primarios (prod por defecto)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "hsomarine")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", "5"))
POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", "10"))

# Valores alternos para entorno local (prefijo LOCAL_*). Si DB_PROFILE==local, reescriben.
LOCAL_POSTGRES_HOST = os.getenv("LOCAL_POSTGRES_HOST")
LOCAL_POSTGRES_PORT = os.getenv("LOCAL_POSTGRES_PORT")
LOCAL_POSTGRES_DB = os.getenv("LOCAL_POSTGRES_DB")
LOCAL_POSTGRES_USER = os.getenv("LOCAL_POSTGRES_USER")
LOCAL_POSTGRES_PASSWORD = os.getenv("LOCAL_POSTGRES_PASSWORD")
LOCAL_POSTGRES_POOL_SIZE = os.getenv("LOCAL_POSTGRES_POOL_SIZE")
LOCAL_POSTGRES_MAX_OVERFLOW = os.getenv("LOCAL_POSTGRES_MAX_OVERFLOW")

if DB_PROFILE == "local":
	if LOCAL_POSTGRES_HOST: POSTGRES_HOST = LOCAL_POSTGRES_HOST
	if LOCAL_POSTGRES_PORT: POSTGRES_PORT = int(LOCAL_POSTGRES_PORT)
	if LOCAL_POSTGRES_DB: POSTGRES_DB = LOCAL_POSTGRES_DB
	if LOCAL_POSTGRES_USER: POSTGRES_USER = LOCAL_POSTGRES_USER
	if LOCAL_POSTGRES_PASSWORD: POSTGRES_PASSWORD = LOCAL_POSTGRES_PASSWORD
	if LOCAL_POSTGRES_POOL_SIZE: POSTGRES_POOL_SIZE = int(LOCAL_POSTGRES_POOL_SIZE)
	if LOCAL_POSTGRES_MAX_OVERFLOW: POSTGRES_MAX_OVERFLOW = int(LOCAL_POSTGRES_MAX_OVERFLOW)

# --- JWT ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "0"))  # 0 días para forzar expiración corta

# Expiración en minutos para sesiones muy cortas (1 minuto)
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "1"))
# Audience fija para los tokens emitidos por esta API (previene replay cross-audience)
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "hso.api")

# --- Sesiones / Cache ---
# TTL de cache para sesiones activas por sid (segundos)
SESSION_CACHE_TTL: int = int(os.getenv("SESSION_CACHE_TTL", "60"))

# --- Rate limit Auth ---
AUTH_RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "300"))
AUTH_RATE_LIMIT_MAX_ATTEMPTS: int = int(os.getenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "10"))

# --- Auth cookies (opcional) ---
# Si está activo, los endpoints de auth además de responder JSON, setearán cookies HttpOnly
# con access_token y refresh_token. Las cookies se llaman 'access_token' y 'refresh_token'.
AUTH_COOKIES_ENABLED: bool = os.getenv("AUTH_COOKIES_ENABLED", "false").lower() in ("1", "true", "yes", "on")
COOKIE_DOMAIN: str | None = os.getenv("COOKIE_DOMAIN")  # ej: .example.com
COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes", "on")
COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")  # lax|strict|none

# --- Static auth fallback (solo pruebas). Ya no requiere flag; si hay email+password se usa. ---
STATIC_AUTH_ENABLED: bool = os.getenv("STATIC_AUTH_ENABLED", "false").lower() in ("1", "true", "yes", "on")  # mantenido por retrocompatibilidad
STATIC_AUTH_EMAIL: str | None = os.getenv("STATIC_AUTH_EMAIL")
STATIC_AUTH_PASSWORD: str | None = os.getenv("STATIC_AUTH_PASSWORD")

# --- Google OAuth ---
GOOGLE_CLIENT_ID: str | None = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI: str | None = os.getenv("GOOGLE_REDIRECT_URI")
# Frontend URL used to redirect users after OAuth when not using popup. Change in .env if needed.
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
# Public app URL (alias for compatibility with docs/integrations)
APP_PUBLIC_URL: str = os.getenv("APP_PUBLIC_URL", FRONTEND_URL)
ODOO_WEBHOOK_SECRET: str = os.getenv("ODOO_WEBHOOK_SECRET", "")
OD00_WEBHOOK_DEDUPE_TTL = os.getenv("OD00_WEBHOOK_DEDUPE_TTL")  # legado typo guard
ODOO_WEBHOOK_DEDUPE_TTL: int = int(os.getenv("ODOO_WEBHOOK_DEDUPE_TTL", OD00_WEBHOOK_DEDUPE_TTL or "600"))
# Opcional: lista blanca de IPs para el webhook (separadas por coma)
ODOO_WEBHOOK_IP_WHITELIST: List[str] = _list_from_env("ODOO_WEBHOOK_IP_WHITELIST", "")
	
# --- Email / SMTP ---
# Dirección por defecto del remitente (From)
EMAIL_SENDER: str | None = os.getenv("EMAIL_SENDER")
# Dirección(es) destino para notificaciones del formulario (separadas por coma)
EMAIL_TO: List[str] = _list_from_env("EMAIL_TO", os.getenv("EMAIL_TO", ""))
# Dirección(es) en copia (CC) para notificaciones del formulario (separadas por coma)
SMTP_CC: List[str] = _list_from_env("SMTP_CC", os.getenv("SMTP_CC", ""))
# Config SMTP
SMTP_HOST: str | None = os.getenv("SMTP_HOST")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str | None = os.getenv("SMTP_USER")
SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
# Si SMTP_SSL es true, se usará conexión SSL directa (puerto típico 465)
SMTP_SSL: bool = os.getenv("SMTP_SSL", "false").lower() in ("1", "true", "yes", "on")
# Si SMTP_TLS es true, se hará STARTTLS en SMTP plano (puerto típico 587)
SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() in ("1", "true", "yes", "on")

# --- Contact form recipients ---
# CONTACT_FORM_TO si está definido tiene prioridad sobre EMAIL_TO
CONTACT_FORM_TO: List[str] = _list_from_env("CONTACT_FORM_TO", os.getenv("CONTACT_FORM_TO", ""))
CONTACT_FORM_CC: List[str] = _list_from_env("CONTACT_FORM_CC", os.getenv("CONTACT_FORM_CC", ""))

# --- Remote App Switch (Vercel mini-backend) ---
# If REMOTE_STATUS_URL is set, requests to protected areas will be allowed only when it returns {"enabled": true}
REMOTE_STATUS_URL: str | None = os.getenv("REMOTE_STATUS_URL")
# Cache TTL (seconds) to avoid hitting the remote on every request
REMOTE_STATUS_CACHE_TTL: int = int(os.getenv("REMOTE_STATUS_CACHE_TTL", "15"))
# Fail-open behavior: if the remote check fails (timeout/network), treat as enabled when True
REMOTE_STATUS_FAIL_OPEN: bool = os.getenv("REMOTE_STATUS_FAIL_OPEN", "true").lower() in ("1", "true", "yes", "on")

# --- Feature flags (activar/desactivar módulos según el proyecto) ---
# Desactivamos por defecto integraciones heredadas del proyecto pasado; pueden habilitarse vía .env si se requieren
ENABLE_ODOO_INTEGRATION: bool = os.getenv("ENABLE_ODOO_INTEGRATION", "false").lower() in ("1", "true", "yes", "on")
ENABLE_GOOGLE_OAUTH: bool = os.getenv("ENABLE_GOOGLE_OAUTH", "false").lower() in ("1", "true", "yes", "on")
ENABLE_CONTACT_FORMS: bool = os.getenv("ENABLE_CONTACT_FORMS", "true").lower() in ("1", "true", "yes", "on")
ENABLE_SUPPORT_FORM: bool = os.getenv("ENABLE_SUPPORT_FORM", "true").lower() in ("1", "true", "yes", "on")
ENABLE_RELEASES_API: bool = os.getenv("ENABLE_RELEASES_API", "true").lower() in ("1", "true", "yes", "on")
ENABLE_RPC_API: bool = os.getenv("ENABLE_RPC_API", "false").lower() in ("1", "true", "yes", "on")
