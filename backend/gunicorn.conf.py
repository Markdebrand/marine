import multiprocessing
import os

bind = "0.0.0.0:8000"
# Socket.IO requiere sticky sessions o un backend de pub/sub; limitamos workers por defecto
# a 1 para evitar handshakes 400/403 cuando no hay Redis manager disponible.
workers = int(os.getenv("WEB_CONCURRENCY", "1")) or 1
# Permitir ajustar manualmente hacia arriba sin perder el tope anterior.
if workers < 1:
	workers = 1
workers = min(workers, max(1, 2 * multiprocessing.cpu_count() + 1))
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"
loglevel = "info"
# Timeout generoso por integraciones externas (p. ej. Odoo)
timeout = 240
