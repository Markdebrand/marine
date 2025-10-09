"""
Conector genérico para Odoo vía XML-RPC.

Responsabilidades:
- Autenticación y transporte XML-RPC con timeout y reintentos.
- Ejecución segura de `execute_kw`.
- Utilidades genéricas (obtener zona horaria, sanitizar campos).
- Métodos genéricos: `search_count`, `search_read`, `read`, `read_group`.

La lógica de negocio debe residir en servicios (p. ej., `odoo_service`).
"""
import xmlrpc.client
from urllib.parse import urlsplit, urlunsplit
from functools import lru_cache
import threading
import time
from typing import Any, cast
import logging
from app.utils.metrics import increment, Timer

from app.config.settings import (
    ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD, ODOO_TIMEOUT,
    ODOO_MAX_RETRIES, ODOO_RETRY_BACKOFF,
)
from app.utils.exceptions import OdooServiceError


class OdooConfigError(RuntimeError):
    """Errores de configuración / autenticación de Odoo."""
    pass


def _require(value: Any, name: str) -> Any:
    if not value:
        raise OdooConfigError(f"Falta variable de entorno/configuración Odoo: {name}")
    return value


class _TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout: int = ODOO_TIMEOUT):
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host):  # type: ignore[override]
        conn = super().make_connection(host)
        try:
            conn.timeout = self.timeout
        except Exception:
            pass
        return conn


_thread_local = threading.local()

@lru_cache(maxsize=1)
def _get_base_url(url: str) -> str:
    raw = url.strip()
    if not raw:
        return ""
    s = urlsplit(raw)
    # Quitar sufijo '/odoo' del path para usar endpoints XML-RPC estándar '/xmlrpc/2/*'
    path = s.path or ""
    if path.endswith("/odoo"):
        path = path[: -len("/odoo")]
    if path.endswith("/odoo/"):
        path = path[: -len("/odoo/")]
    # Normalizar múltiples '/'
    if path == "/":
        path = ""
    base = urlunsplit((s.scheme, s.netloc, path.rstrip("/"), "", ""))
    return base.rstrip("/")

def _get_proxies_threadlocal(url: str):
    """Devuelve proxies xmlrpc (common, models) por hilo, con timeout y allow_none.

    Evita compartir ServerProxy entre hilos para reducir race conditions.
    """
    base = _get_base_url(url)
    if not hasattr(_thread_local, "proxies"):
        _thread_local.proxies = {}
    proxies = _thread_local.proxies  # type: ignore[attr-defined]
    if base in proxies:
        return proxies[base]
    transport = _TimeoutTransport(timeout=ODOO_TIMEOUT)
    common = xmlrpc.client.ServerProxy(f"{base}/xmlrpc/2/common", allow_none=True, transport=transport)
    models = xmlrpc.client.ServerProxy(f"{base}/xmlrpc/2/object", allow_none=True, transport=transport)
    proxies[base] = (common, models)
    return proxies[base]


class OdooConnector:
    """Conector Odoo con timeout, reintentos y utilidades genéricas."""

    def __init__(
        self,
        url: str | None = None,
        db: str | None = None,
        username: str | None = None,
        password: str | None = None,
        *,
        eager: bool = False,
    ):
        self.url = _require(url or ODOO_URL, "ODOO_URL")
        self.db = _require(db or ODOO_DB, "ODOO_DB")
        self.username = _require(username or ODOO_USER, "ODOO_USER")
        self.password = _require(password or ODOO_PASSWORD, "ODOO_PASSWORD")
        self._uid: int | None = None
        self._tz: str | None = None
        self._lock = threading.Lock()
        # Cache simple de campos por modelo -> set[str]
        self._model_fields: dict[str, set[str]] = {}
        if eager:
            self.authenticate()

    def authenticate(self, *, force: bool = False) -> int:
        if force or self._uid is None:
            common, _ = _get_proxies_threadlocal(self.url)
            uid = cast(int, common.authenticate(self.db, self.username, self.password, {}))
            if not uid:
                raise OdooConfigError("Autenticación Odoo fallida: uid vacío")
            self._uid = uid
        return self._uid  # type: ignore[return-value]

    @property
    def uid(self) -> int:
        return self.authenticate()

    @property
    def models(self):
        _common, models = _get_proxies_threadlocal(self.url)
        return models

    @property
    def common(self):
        common, _models = _get_proxies_threadlocal(self.url)
        return common

    def server_version(self) -> dict:
        """Devuelve información de versión del servidor Odoo.

        Usa el endpoint xmlrpc /common que expone `version`.
        """
        return cast(dict, getattr(self.common, "version")())

    # --- Wrapper robusto con reintentos y backoff ---
    def _execute_kw(self, model: str, method: str, args: list, kwargs: dict | None = None, *, allow_retry: bool = True):
        kwargs = kwargs or {}
        attempt = 0
        last_exc: Exception | None = None
        logger = logging.getLogger("app.integrations.odoo")
        tags = {"model": model, "method": method}
        while True:
            try:
                with Timer("odoo.execute", tags=tags):
                    return self.models.execute_kw(self.db, self.uid, self.password, model, method, args, kwargs)
            except xmlrpc.client.Fault as e:
                # Fault: error lógico del servidor Odoo -> no tiene sentido reintentar
                last_exc = e
                increment("odoo.execute.error", tags={**tags, "kind": e.__class__.__name__})
                logger.error(
                    f"Odoo RPC fault {model}.{method}: {e}",
                    extra={"error": str(e), **tags},
                )
                break
            except (xmlrpc.client.ProtocolError, OdooServiceError, ConnectionError, TimeoutError) as e:
                last_exc = e
                attempt += 1
                increment("odoo.execute.error", tags={**tags, "kind": e.__class__.__name__})
                if not allow_retry or attempt > max(1, ODOO_MAX_RETRIES):
                    break
                # Backoff exponencial con jitter ligero
                sleep_s = (ODOO_RETRY_BACKOFF * (2 ** (attempt - 1))) * (1 + 0.1 * (attempt % 3))
                try:
                    time.sleep(min(sleep_s, 3.0))
                except Exception:
                    pass
                # Forzar reautenticación en siguientes intentos por si expiró la sesión
                try:
                    self.authenticate(force=True)
                except Exception as auth_err:
                    logger.warning("Odoo re-auth failed", extra={"error": str(auth_err), **tags})
                logger.warning(
                    f"Odoo RPC retry {model}.{method} (attempt={attempt}, sleep={round(sleep_s,3)}s): {e}",
                    extra={"attempt": attempt, "sleep": round(sleep_s, 3), "error": str(e), **tags},
                )
                continue
            except Exception as e:
                # errores no previstos -> sin reintento para no ocultar fallas lógicas
                logger.exception(f"Odoo RPC unexpected error {model}.{method}: {e}", extra={"error": str(e), **tags})
                raise e
        # Si llegó aquí, no se pudo recuperar
        logger.error(
            f"Odoo RPC failed after retries {model}.{method}: {last_exc}",
            extra={"attempts": attempt, "last_error": str(last_exc) if last_exc else None, **tags},
        )
        increment("odoo.execute.failed", tags=tags)
        raise OdooServiceError(f"Fallo Odoo {model}.{method} tras reintentos", details={"args": args, "kwargs": kwargs}) from last_exc

    # --- Métodos genéricos ---
    def get_context_with_tz(self, base: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(base or {})
        tz = self.get_user_tz()
        if tz:
            ctx["tz"] = tz
        return ctx

    def search_count(self, model: str, domain: list | None = None, *, context: dict[str, Any] | None = None) -> int:
        domain = domain or []
        return cast(int, self._execute_kw(model, "search_count", [domain], {"context": context or {}}))

    def search_read(
        self,
        model: str,
        domain: list | None = None,
        *,
        fields: list[str] | None = None,
        order: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        domain = domain or []
        kwargs: dict[str, Any] = {}
        if fields is not None:
            safe_fields = self._sanitize_fields(model, fields)
            if safe_fields:
                kwargs["fields"] = safe_fields
        if order is not None:
            kwargs["order"] = order
        if limit is not None:
            kwargs["limit"] = limit
        if offset is not None:
            kwargs["offset"] = offset
        if context is not None:
            kwargs["context"] = context
        return cast(list[dict[str, Any]], self._execute_kw(model, "search_read", [domain], kwargs))

    def read(
        self,
        model: str,
        ids: list[int],
        *,
        fields: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        args: list[Any] = [ids]
        if fields is not None:
            safe_fields = self._sanitize_fields(model, fields)
            if safe_fields:
                args.append(safe_fields)
        kwargs: dict[str, Any] = {}
        if context is not None:
            kwargs["context"] = context
        return cast(list[dict[str, Any]], self._execute_kw(model, "read", args, kwargs))

    def read_group(
        self,
        model: str,
        domain: list | None,
        fields: list[str],
        groupby: list[str],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        domain = domain or []
        kwargs: dict[str, Any] = {}
        if context is not None:
            kwargs["context"] = context
        return cast(list[dict[str, Any]], self._execute_kw(model, "read_group", [domain, fields, groupby], kwargs))

    # --- Utilidad: zona horaria de usuario para que coincida con la UI ---
    def get_user_tz(self) -> str | None:
        if self._tz is not None:
            return self._tz
        logger = logging.getLogger("app.integrations.odoo")
        try:
            res = cast(list[dict[str, Any]], self._execute_kw(
                "res.users", "read",
                [[self.uid], ["tz"]],
                {}
            ))
            tz_raw = (res and res[0].get("tz")) or None
            tz: str | None = None
            if tz_raw is not None:
                tz = str(tz_raw)
            self._tz = tz
            return tz
        except Exception as e:
            # Si no podemos obtener la TZ del usuario, continuamos sin ella
            logger.warning("get_user_tz failed; proceeding without tz", extra={"error": str(e)})
            self._tz = None
            return None

    # --- Internals ---
    def _sanitize_fields(self, model: str, requested: list[str]) -> list[str]:
        try:
            available = self._get_model_fields(model)
            return [f for f in requested if f in available]
        except Exception as e:
            logging.getLogger("app.integrations.odoo").warning(
                "fields_get failed; using requested fields as-is",
                extra={"model": model, "error": str(e)},
            )
            # Devolver lista vacía para no pasar 'fields' y evitar Fault
            return []

    def _get_model_fields(self, model: str) -> set[str]:
        if model in self._model_fields:
            return self._model_fields[model]
        # fields_get devuelve dict campo -> {type, string, ...}
        # Usar kwargs 'attributes' para compatibilidad con versiones modernas
        res = cast(
            dict[str, dict[str, Any]],
            self._execute_kw(model, "fields_get", [], {"attributes": ["string"]})
        )
        names = set(res.keys()) if isinstance(res, dict) else set()
        self._model_fields[model] = names
        return names
