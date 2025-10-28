from dotenv import load_dotenv
import os
from typing import List
from pathlib import Path
import json
import logging
from urllib.parse import urlsplit

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


def _int_from_env(var_name: str) -> int | None:
	value = os.getenv(var_name)
	if value is None or value.strip() == "":
		return None
	try:
		return int(value)
	except ValueError:
		return None


def _float_from_env(var_name: str) -> float | None:
	value = os.getenv(var_name)
	if value is None or value.strip() == "":
		return None
	try:
		return float(value)
	except ValueError:
		return None


def _normalize_origin(origin: str) -> str | None:
	origin = (origin or "").strip()
	if not origin:
		return None
	if origin == "*":
		return origin
	try:
		parts = urlsplit(origin)
	except ValueError:
		return origin
	if parts.scheme and parts.netloc:
		return f"{parts.scheme}://{parts.netloc}"
	return origin


def _append_origin(origins: List[str], origin: str | None) -> None:
	if not origin:
		return
	norm = _normalize_origin(origin)
	if norm and norm not in origins:
		origins.append(norm)


# --- App settings ---
APP_NAME: str = os.getenv("APP_NAME", "HSOMarine API")
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes", "on")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
ROOT_PATH: str = os.getenv("ROOT_PATH", "")

# CORS y seguridad
# Por defecto permitimos localhost:3000 y 127.0.0.1:3000 (Next.js) en desarrollo si no se define CORS_ORIGINS
CORS_ORIGINS: List[str] = _list_from_env("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_normalized_origins: List[str] = []
for _origin in CORS_ORIGINS:
	norm = _normalize_origin(_origin)
	if not norm:
		continue
	if norm not in _normalized_origins:
		_normalized_origins.append(norm)
CORS_ORIGINS = _normalized_origins
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
_redis_pool_max_connections_raw = _int_from_env("REDIS_POOL_MAX_CONNECTIONS")
if _redis_pool_max_connections_raw is None:
	REDIS_POOL_MAX_CONNECTIONS: int | None = 200
elif _redis_pool_max_connections_raw <= 0:
	REDIS_POOL_MAX_CONNECTIONS = None
else:
	REDIS_POOL_MAX_CONNECTIONS = _redis_pool_max_connections_raw
REDIS_POOL_SOCKET_TIMEOUT: float | None = _float_from_env("REDIS_POOL_SOCKET_TIMEOUT")
REDIS_POOL_SOCKET_CONNECT_TIMEOUT: float | None = _float_from_env("REDIS_POOL_SOCKET_CONNECT_TIMEOUT")
REDIS_POOL_HEALTH_CHECK_INTERVAL: int | None = _int_from_env("REDIS_POOL_HEALTH_CHECK_INTERVAL")
REDIS_POOL_RETRY_ON_TIMEOUT: bool = os.getenv("REDIS_POOL_RETRY_ON_TIMEOUT", "true").lower() in ("1", "true", "yes", "on")

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
	if LOCAL_POSTGRES_HOST:
		POSTGRES_HOST = LOCAL_POSTGRES_HOST
	if LOCAL_POSTGRES_PORT:
		POSTGRES_PORT = int(LOCAL_POSTGRES_PORT)
	if LOCAL_POSTGRES_DB:
		POSTGRES_DB = LOCAL_POSTGRES_DB
	if LOCAL_POSTGRES_USER:
		POSTGRES_USER = LOCAL_POSTGRES_USER
	if LOCAL_POSTGRES_PASSWORD:
		POSTGRES_PASSWORD = LOCAL_POSTGRES_PASSWORD
	if LOCAL_POSTGRES_POOL_SIZE:
		POSTGRES_POOL_SIZE = int(LOCAL_POSTGRES_POOL_SIZE)
	if LOCAL_POSTGRES_MAX_OVERFLOW:
		POSTGRES_MAX_OVERFLOW = int(LOCAL_POSTGRES_MAX_OVERFLOW)

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
# Single session policy: 'block' (default) will prevent new logins if an active session exists.
# 'force' will revoke existing active sessions and allow the new login to proceed.
SINGLE_SESSION_POLICY: str = os.getenv("SINGLE_SESSION_POLICY", "block")

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
STATIC_AUTH_ROLE: str = os.getenv("STATIC_AUTH_ROLE", "user").strip().lower() or "user"
if STATIC_AUTH_ROLE not in ("admin", "user", "cliente"):
	STATIC_AUTH_ROLE = "user"
STATIC_AUTH_SUPERADMIN: bool = os.getenv("STATIC_AUTH_SUPERADMIN", "false").lower() in ("1", "true", "yes", "on")

# En producción, desactivar fallback estático por seguridad salvo que explícitamente se active en .env
if not DEBUG:
	STATIC_AUTH_ENABLED = False

# Validación mínima de secretos críticos en tiempo de carga para evitar arranques inseguros
_log = logging.getLogger("settings")
if not DEBUG and (not JWT_SECRET_KEY or JWT_SECRET_KEY in ("change-me", "default", "")):
	raise RuntimeError("JWT_SECRET_KEY must be set to a secure value in production")
if not DEBUG and not COOKIE_SECURE:
	_log.warning("COOKIE_SECURE is False in non-DEBUG mode; consider setting COOKIE_SECURE=true in production env")

# --- Google OAuth ---
GOOGLE_CLIENT_ID: str | None = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI: str | None = os.getenv("GOOGLE_REDIRECT_URI")
# Frontend URL used to redirect users after OAuth when not using popup. Change in .env if needed.
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
_append_origin(CORS_ORIGINS, FRONTEND_URL)
# Public app URL (alias for compatibility with docs/integrations)
APP_PUBLIC_URL: str = os.getenv("APP_PUBLIC_URL", FRONTEND_URL)
_append_origin(CORS_ORIGINS, APP_PUBLIC_URL)
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

# --- AIS Simulator (Socket.IO) ---
# Activa el simulador en desarrollo por defecto; en producción queda desactivado salvo que se fuerce.
AISSTREAM_ENABLED: bool = os.getenv("AISSTREAM_ENABLED", "true").lower() in ("1", "true", "yes", "on")
AISSTREAM_API_KEY: str | None = os.getenv("AISSTREAM_API_KEY")

# Opciones adicionales para AISStream
def _parse_bbox_env(name: str):
	raw = os.getenv(name, "") or ""
	if not raw:
		return None
	try:
		val = json.loads(raw)
		# Expecting [[min_lat,min_lon],[max_lat,max_lon]] or similar
		return val
	except Exception:
		# Fallback: comma-separated min_lat,min_lon,max_lat,max_lon
		parts = [p.strip() for p in raw.split(",") if p.strip()]
		if len(parts) == 4:
			return [[float(parts[0]), float(parts[1])], [float(parts[2]), float(parts[3])]]
	return None

AISSTREAM_BOUNDING_BOXES = _parse_bbox_env("AISSTREAM_BOUNDING_BOXES") or [[-90.0, -180.0], [90.0, 180.0]]
AISSTREAM_FILTER_MMSI = [x.strip() for x in (os.getenv("AISSTREAM_FILTER_MMSI", "") or "").split(",") if x.strip()]
AISSTREAM_FILTER_TYPES = [x.strip() for x in (os.getenv("AISSTREAM_FILTER_TYPES", "PositionReport") or "").split(",") if x.strip()]
AISSTREAM_BATCH_MS: int = int(os.getenv("AISSTREAM_BATCH_MS", "0"))

# Singleton lock (opcional) para evitar múltiples trabajadores conectando al feed.
AISSTREAM_SINGLETON_LOCK_KEY: str = os.getenv("AISSTREAM_SINGLETON_LOCK_KEY", "aisstream_bridge_lock")
AISSTREAM_SINGLETON_LOCK_TTL: int = int(os.getenv("AISSTREAM_SINGLETON_LOCK_TTL", "60"))
