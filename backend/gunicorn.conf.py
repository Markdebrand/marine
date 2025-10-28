import multiprocessing

bind = "0.0.0.0:8000"
# Con Redis como message queue para Socket.IO podemos volver a calcular workers
# en función del número de CPUs.
workers = min(2 * multiprocessing.cpu_count() + 1, 8)
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"
loglevel = "info"
# Timeout generoso por integraciones externas (p. ej. Odoo)
timeout = 240
