
"""
Manejadores globales de errores para FastAPI.
"""
import logging
from fastapi import Request, FastAPI, status, HTTPException
from fastapi.responses import JSONResponse
from typing import Any
from .exceptions import ExternalServiceError

def add_global_exception_handler(app: FastAPI) -> None:
    """Agrega un handler global para excepciones no capturadas."""
    # Preservar HTTPException (401/403/404/etc.)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> Any:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    # Manejo específico de servicios externos
    @app.exception_handler(ExternalServiceError)
    async def external_service_exception_handler(request: Request, exc: ExternalServiceError) -> Any:
        logging.error(f"External service error [{exc.service}]: {exc}")
        payload = {
            "error": exc.code,
            "service": exc.service,
            "message": str(exc),
            "details": exc.details,
        }
        return JSONResponse(status_code=exc.status_code, content=payload)

    # Manejo genérico para otras excepciones no controladas
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> Any:
        logging.exception("Unhandled error")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": "unhandled_exception",
                "message": "Internal server error. Please try again later.",
                "path": str(request.url.path),
                "method": request.method,
            }
        )
