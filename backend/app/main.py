
from contextlib import asynccontextmanager
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
    try:
        init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"DB init failed: {e}")
    yield

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
