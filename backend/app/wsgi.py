"""
Adaptador WSGI para ejecutar la app FastAPI (ASGI) bajo Apache mod_wsgi.

En producción es más eficiente usar Gunicorn/Uvicorn detrás de Apache/Nginx
(reverse proxy). Este archivo existe para compatibilidad con mod_wsgi.
"""

from asgiref.wsgi import AsgiToWsgi # type: ignore
from app.main import app as asgi_app

# Objeto WSGI que Apache/mod_wsgi espera
application = AsgiToWsgi(asgi_app)

