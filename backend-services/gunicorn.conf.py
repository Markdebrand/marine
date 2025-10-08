bind = "0.0.0.0:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
# Ajusta según CPU/RAM: workers = 2 * cores + 1
accesslog = "-"
errorlog = "-"
loglevel = "info"
# timeout generoso si Odoo responde lento
timeout = 240