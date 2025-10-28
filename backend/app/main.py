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
    # NOTA: El orden de adición es importante en Starlette; el último añadido es el más externo.
    # Para que CORS envuelva TODAS las respuestas (incluyendo errores tempranos de otros middlewares
    # y preflight OPTIONS), añadiremos CORSMiddleware al final.
    # TrustedHost solo en entornos no-DEBUG para evitar problemas en desarrollo
    from app.config.settings import DEBUG
    if ALLOWED_HOSTS and not DEBUG:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
    app.add_middleware(GZipMiddleware, minimum_size=500)
    # Correlation-ID para trazabilidad
    app.add_middleware(RequestIdMiddleware)
    # Interruptor remoto de disponibilidad (antes de auth para bloquear pronto)
    app.add_middleware(AppSwitchMiddleware)
    # Auth context: decode JWT once and attach payload to request.state
    app.add_middleware(AuthContextMiddleware)
    # Require auth for protected prefixes while keeping public endpoints open
    app.add_middleware(RequireAuthMiddleware)
    # Auditoría privada de requests
    app.add_middleware(AuditMiddleware)
    # Finalmente, CORS como el más externo para asegurar headers en todas las respuestas
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
    sio_server = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
    sio_asgi = socketio.ASGIApp(sio_server, socketio_path="/socket.io")
    app.state.sio_server = sio_server
    app.state.sio_asgi = sio_asgi
    # Basic Socket.IO connect/disconnect logs to debug connection churn

    @sio_server.event
    async def connect(sid, environ, auth=None):  # noqa: ANN001
        logging.getLogger("socketio").info(f"[SOCKET.IO] client connected sid={sid} from {environ.get('REMOTE_ADDR')}")


    @sio_server.event
    async def disconnect(sid):  # noqa: ANN001
        logging.getLogger("socketio").info(f"[SOCKET.IO] client disconnected sid={sid}")
    try:
        init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"DB init failed: {e}")
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
                redis_client = Redis.from_url(redis_url)
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
