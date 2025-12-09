from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from app.config.settings import (
    APP_NAME,
    LOG_LEVEL,
    CORS_ORIGINS,
    ALLOWED_HOSTS,
    DOCS_URL,
    REDOC_URL,
    OPENAPI_URL,
    ROOT_PATH,
    REDIS_URL,
    REDIS_POOL_MAX_CONNECTIONS,
    REDIS_POOL_SOCKET_TIMEOUT,
    REDIS_POOL_SOCKET_CONNECT_TIMEOUT,
    REDIS_POOL_HEALTH_CHECK_INTERVAL,
    REDIS_POOL_RETRY_ON_TIMEOUT,
)
from app.utils.logging_config import setup_logging
from app.db.database import init_db
from app.utils.exception_handlers import add_global_exception_handler
import socketio
from app.config.settings import AISSTREAM_ENABLED, AISSTREAM_API_KEY, AISSTREAM_SINGLETON_LOCK_KEY, AISSTREAM_SINGLETON_LOCK_TTL
from redis import Redis
import time
from app.integrations.aisstream.service import AISBridgeService

def add_middlewares(app):
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
    from starlette.middleware.gzip import GZipMiddleware
    from app.core.middleware.request_id_middleware import RequestIdMiddleware
    from app.core.middleware.audit_middleware import AuditMiddleware
    from app.core.middleware.auth_middleware import AuthContextMiddleware
    from app.core.middleware.require_auth_middleware import RequireAuthMiddleware
    from app.core.middleware.app_switch_middleware import AppSwitchMiddleware
    from app.config.settings import DEBUG
    
    # ⚠️ ORDEN CRÍTICO: Los middlewares se ejecutan en ORDEN INVERSO al que se añaden
    # El último añadido es el primero en ejecutarse (envuelve a los demás)
    
    # 1. TrustedHost (solo en producción)
    if ALLOWED_HOSTS and not DEBUG:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
    
    # 2. Proxy headers
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
    
    # 3. Compression
    app.add_middleware(GZipMiddleware, minimum_size=500)
    
    # 4. Request ID para trazabilidad
    app.add_middleware(RequestIdMiddleware)
    
    # 5. App switch (antes de auth para bloquear temprano)
    app.add_middleware(AppSwitchMiddleware)
    
    # 6. Auth context: decode JWT and attach to request.state
    app.add_middleware(AuthContextMiddleware)
    
    # 7. Require auth (PERO debe permitir OPTIONS sin auth)
    app.add_middleware(RequireAuthMiddleware)
    
    # 8. Auditoría
    app.add_middleware(AuditMiddleware)
    
    # 🔥 CRITICAL: CORS debe ser el ÚLTIMO middleware añadido (primero en ejecutarse)
    # para que maneje OPTIONS preflight antes que cualquier otro middleware
    if CORS_ORIGINS:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

def add_routers(app):
    # Router centralizado
    from app.api.root_router import router as api_router
    app.include_router(api_router)

def add_dispatcher(app):
    # Ya no usamos middleware de despacho dinámico.
    # La autorización y permisos se gestionan con dependencias por ruta.
    return

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(LOG_LEVEL)
    # Crear Socket.IO server ASGI y adjuntar a app.state
    sio_kwargs = {
        "async_mode": "asgi",
        "cors_allowed_origins": CORS_ORIGINS if CORS_ORIGINS else "*",
    }
    if REDIS_URL:
        try:
            redis_options: dict[str, object] = {}
            if REDIS_POOL_MAX_CONNECTIONS is not None:
                redis_options["max_connections"] = REDIS_POOL_MAX_CONNECTIONS
            if REDIS_POOL_SOCKET_TIMEOUT is not None:
                redis_options["socket_timeout"] = REDIS_POOL_SOCKET_TIMEOUT
            if REDIS_POOL_SOCKET_CONNECT_TIMEOUT is not None:
                redis_options["socket_connect_timeout"] = REDIS_POOL_SOCKET_CONNECT_TIMEOUT
            if REDIS_POOL_HEALTH_CHECK_INTERVAL is not None:
                redis_options["health_check_interval"] = REDIS_POOL_HEALTH_CHECK_INTERVAL
            redis_options["retry_on_timeout"] = REDIS_POOL_RETRY_ON_TIMEOUT
            sio_kwargs["client_manager"] = socketio.AsyncRedisManager(
                REDIS_URL,
                redis_options=redis_options,
            )
            logging.getLogger("socketio").info(
                "Socket.IO Redis client manager enabled with pooled connections",  # noqa: DY001
            )
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("socketio").error(
                "Failed to init Redis client manager: %s", exc,
            )
    sio_server = socketio.AsyncServer(**sio_kwargs)
    sio_asgi = socketio.ASGIApp(sio_server, socketio_path="/socket.io")
    app.state.sio_server = sio_server
    app.state.sio_asgi = sio_asgi
    # Basic Socket.IO connect/disconnect logs to debug connection churn
    @sio_server.event
    async def connect(sid, environ, auth=None):  # noqa: ANN001
        logging.getLogger("socketio").info("client connected sid=%s", sid)

    @sio_server.event
    async def disconnect(sid):  # noqa: ANN001
        logging.getLogger("socketio").info("client disconnected sid=%s", sid)
    try:
        init_db()
    except Exception as e:
        logging.getLogger(__name__).error("DB init failed: %s", e)
    # Si AISStream está habilitado y tiene API key, usamos AISStream en lugar del simulador local
    bridge: AISBridgeService | None = None
    lock_owner = False
    redis_client = None
    try:
        redis_url = getattr(__import__("app.config.settings"), "REDIS_URL", None)
    except Exception:
        redis_url = None
    if AISSTREAM_ENABLED and AISSTREAM_API_KEY:
        # Si hay Redis configurado, intentamos tomar un lock para que SOLO un worker cree la conexión
        if redis_url:
            try:
                redis_kwargs: dict[str, object] = {}
                if REDIS_POOL_MAX_CONNECTIONS is not None:
                    redis_kwargs["max_connections"] = REDIS_POOL_MAX_CONNECTIONS
                if REDIS_POOL_SOCKET_TIMEOUT is not None:
                    redis_kwargs["socket_timeout"] = REDIS_POOL_SOCKET_TIMEOUT
                if REDIS_POOL_SOCKET_CONNECT_TIMEOUT is not None:
                    redis_kwargs["socket_connect_timeout"] = REDIS_POOL_SOCKET_CONNECT_TIMEOUT
                if REDIS_POOL_HEALTH_CHECK_INTERVAL is not None:
                    redis_kwargs["health_check_interval"] = REDIS_POOL_HEALTH_CHECK_INTERVAL
                redis_kwargs["retry_on_timeout"] = REDIS_POOL_RETRY_ON_TIMEOUT
                redis_client = Redis.from_url(redis_url, **redis_kwargs)
                # SETNX con expiración
                lock_key = AISSTREAM_SINGLETON_LOCK_KEY
                now = int(time.time())
                if redis_client.set(lock_key, now, nx=True, ex=AISSTREAM_SINGLETON_LOCK_TTL):
                    lock_owner = True
            except Exception:
                # Si falla Redis, continuamos sin singleton
                redis_client = None
        if not redis_client or lock_owner:
            bridge = AISBridgeService(sio_server, AISSTREAM_API_KEY)
            await bridge.start()
    app.state.ais_bridge = bridge
    yield
    # Apagado ordenado
    if bridge is not None:
        await bridge.stop()

def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        docs_url=DOCS_URL,
        redoc_url=REDOC_URL,
        openapi_url=OPENAPI_URL,
        lifespan=lifespan,
        root_path=ROOT_PATH,
    )
    add_global_exception_handler(app)
    add_middlewares(app)
    add_routers(app)
    # Dispatcher eliminado: autorización via dependencias por endpoint
    return app

app = create_app()

# Montar la app de Socket.IO bajo el mismo servidor ASGI en la ruta /socket.io
# Nota: ASGIApp de socketio funciona como sub-aplicación; FastAPI manejará el resto.
try:
    # No imports extra necesarios; usamos ASGI routing manual

    # Creamos un wrapper ASGI que enruta /socket.io a sio_asgi y el resto a FastAPI
    # Para entornos que lo necesiten (uvicorn acepta una sola app), exponemos una app compuesta
    class RootASGI:
        def __init__(self, fastapi_app: FastAPI):
            self.fastapi_app = fastapi_app

        async def __call__(self, scope, receive, send):  # noqa: ANN001
            if scope["type"] in ("http", "websocket") and scope.get("path", "").startswith("/socket.io"):
                # Despachar a Socket.IO
                sio_asgi = getattr(self.fastapi_app.state, "sio_asgi", None)
                if sio_asgi is not None:
                    await sio_asgi(scope, receive, send)
                    return
            # Fallback a FastAPI
            await self.fastapi_app(scope, receive, send)

    asgi = RootASGI(app)
except Exception:
    # Si por alguna razón falla, al menos la app principal sigue disponible
    asgi = app
