import multiprocessing
import os

bind = "0.0.0.0:8000"
# Calcular workers por defecto (típicamente 2 * cores + 1), cap a 8
_default_workers = min(2 * multiprocessing.cpu_count() + 1, 8)
# Permitir override por variable de entorno para compatibilidad con Socket.IO (polling) sin sticky sessions
# En producción, si no se usa un message queue (Redis) para python-socketio, es recomendable WEB_CONCURRENCY=1
workers = int(os.getenv("WEB_CONCURRENCY", str(_default_workers)))
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"
loglevel = "info"
# Timeout generoso por integraciones externas (p. ej. Odoo)
timeout = 240
