import multiprocessing

bind = "0.0.0.0:8000"
# Calcular workers basados en CPUs (típicamente 2 * cores + 1), pero cap a 8
workers = min(2 * multiprocessing.cpu_count() + 1, 8)
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"
loglevel = "info"
# Timeout generoso por integraciones externas (p. ej. Odoo)
timeout = 240
