
"""
Configuración de logging para la aplicación.
"""
import logging
import logging.config
import os

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        import json
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Extras comunes
        cid = getattr(record, "correlation_id", None)
        if cid:
            payload["correlation_id"] = cid
        return json.dumps(payload, ensure_ascii=False)

def setup_logging(level: str = "INFO") -> None:
    """Configura el logging global de la app y servidores ASGI."""
    fmt = os.getenv("LOG_FORMAT", "text").lower()
    is_json = fmt == "json"
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": JsonFormatter if is_json else logging.Formatter,
                    "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
                },
                "access": {
                    "()": JsonFormatter if is_json else logging.Formatter,
                    "format": '%(asctime)s %(levelname)s %(name)s - "%(message)s"',
                },
            },
            "handlers": {
                "default": {"class": "logging.StreamHandler", "formatter": "default"},
                "access": {"class": "logging.StreamHandler", "formatter": "access"},
            },
            "loggers": {
                "": {"handlers": ["default"], "level": level},
                "uvicorn": {"handlers": ["default"], "level": level, "propagate": False},
                "uvicorn.error": {"level": level, "handlers": ["default"], "propagate": False},
                "uvicorn.access": {"handlers": ["access"], "level": level, "propagate": False},
                "gunicorn.error": {"handlers": ["default"], "level": level, "propagate": False},
                "gunicorn.access": {"handlers": ["access"], "level": level, "propagate": False},
                "app": {"handlers": ["default"], "level": level, "propagate": False},
                "app.request": {"handlers": ["default"], "level": level, "propagate": False},
                "app.auth": {"handlers": ["default"], "level": level, "propagate": False},
                "app.audit": {"handlers": ["default"], "level": level, "propagate": False},
            },
        }
    )
