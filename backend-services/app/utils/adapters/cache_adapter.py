
"""
Cache con TTL con backend dual: in-memory (por defecto) o Redis si REDIS_URL está configurado.

- Seguro para multi-worker cuando se usa Redis.
- Resiliente: si Redis falla, hace fallback a memoria sin romper el flujo.
"""
import time
import logging
import pickle
from typing import Any, Optional, Callable, TypeVar, Tuple, Dict, cast
from functools import wraps

from app.config.settings import REDIS_URL, APP_NAME

logger = logging.getLogger("app.utils.cache")

# --- In-memory store (fallback) ---
_store: Dict[str, Tuple[float, Any]] = {}

# --- Redis (opcional) ---
_redis = None  # tipo dinámico para evitar dependencia dura
_redis_enabled = False
_CACHE_PREFIX = f"{(APP_NAME or 'app').lower().replace(' ', '-')}:cache:"  # namespace

try:
    if REDIS_URL:
        import redis  # type: ignore

        _redis = redis.Redis.from_url(REDIS_URL, decode_responses=False)
        # Ping non-bloqueante (tolerante a error)
        try:
            _redis.ping()
            _redis_enabled = True
            logger.info("Cache backend: Redis habilitado", extra={"url": REDIS_URL})
        except Exception as e:  # pragma: no cover - entorno sin Redis
            logger.warning("Redis no disponible, usando cache en memoria", extra={"error": str(e)})
            _redis_enabled = False
except Exception as e:  # pragma: no cover
    logger.debug("Paquete redis no instalado o error iniciando Redis", extra={"error": str(e)})
    _redis_enabled = False

T = TypeVar("T")


def _now() -> float:
    return time.time()


def _mkey(key: str) -> str:
    return f"{_CACHE_PREFIX}{key}"


def _serialize(value: Any) -> bytes:
    return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)


def _deserialize(data: bytes) -> Any:
    return pickle.loads(data)


def set_cache(key: str, value: Any, ttl_seconds: int) -> None:
    """Guarda un valor en caché con TTL en segundos. Usa Redis si está disponible."""
    ttl = max(0, int(ttl_seconds))
    # Siempre escribir en memoria (backup local)
    _store[_mkey(key)] = (_now() + ttl, value)
    if not _redis_enabled or _redis is None or ttl == 0:
        return
    try:
        _redis.set(name=_mkey(key), value=_serialize(value), ex=ttl)
    except Exception as e:  # Fallback silencioso a memoria
        logger.warning("Error escribiendo en Redis cache", extra={"key": key, "error": str(e)})


def get_cache(key: str) -> Optional[Any]:
    """Obtiene un valor del caché si no ha expirado. Prefiere Redis si está disponible."""
    # Intentar Redis primero
    if _redis_enabled and _redis is not None:
        try:
            raw = _redis.get(_mkey(key))
            if raw is not None:
                try:
                    val = _deserialize(raw) # pyright: ignore[reportArgumentType]
                    # Opcional: propagar a memoria para acceso local rápido
                    _store[_mkey(key)] = (_now() + 60, val)  # pequeño TTL de sombra
                    return val
                except Exception:
                    # Si no se puede deserializar, borrar y seguir con memoria
                    _redis.delete(_mkey(key))
        except Exception as e:
            logger.warning("Error leyendo de Redis cache", extra={"key": key, "error": str(e)})
    # Fallback a memoria
    item = _store.get(_mkey(key))
    if not item:
        return None
    expires_at, value = item
    if _now() >= expires_at:
        _store.pop(_mkey(key), None)
        return None
    return value


def clear_cache(prefix: Optional[str] = None) -> None:
    """Limpia el caché completo o sólo claves con prefijo.

    En Redis, usa SCAN para evitar bloquear.
    """
    p = _mkey(prefix or "")
    # Limpiar memoria
    if not prefix:
        for k in list(_store.keys()):
            if k.startswith(_CACHE_PREFIX):
                _store.pop(k, None)
    else:
        for k in list(_store.keys()):
            if k.startswith(p):
                _store.pop(k, None)
    # Limpiar Redis
    if _redis_enabled and _redis is not None:
        try:
            pattern = f"{p}*" if prefix else f"{_CACHE_PREFIX}*"
            # scan_iter es lazy y seguro
            keys = list(_redis.scan_iter(match=pattern, count=500))
            if keys:
                _redis.delete(*keys)
        except Exception as e:
            logger.warning("Error limpiando Redis cache", extra={"prefix": prefix, "error": str(e)})


def cacheable(ttl_seconds: int = 60):
    """Decorador para cachear el resultado de una función según sus argumentos.

    Nota: la clave se construye con str(args/kwargs); asegúrate de no incluir
    objetos no determinísticos o secretos en los argumentos.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            key = f"{func.__module__}.{func.__name__}:{args}:{tuple(sorted(kwargs.items()))}"
            cached = get_cache(key)
            if cached is not None:
                return cast(T, cached)
            result = func(*args, **kwargs)
            set_cache(key, result, ttl_seconds)
            return result
        return wrapper
    return decorator


def is_redis_enabled() -> bool:
    """Indica si el backend Redis está activo."""
    return bool(_redis_enabled and _redis is not None)
