# Despliegue en Portainer (HSOMarine: Test y Producción)

Este repo ya está adaptado a HSOMarine y a Postgres. Contiene `docker-compose.test.yml` y `docker-compose.prod.yml` para crear dos Stacks en Portainer: uno de pruebas (staging) y otro de producción.

## Requisitos

- Acceso a Portainer con permisos para crear Stacks y volúmenes.
- No necesitas acceso al VPS por SSH.
- Tener a mano las variables de entorno de test y prod. En este repo ya existen plantillas: `variables.env.test` y `variables.env.production` (revisa y actualiza valores sensibles antes de usarlos).

## Arquitectura

- `frontend`: Nginx sirviendo el build de Next.js. Expone puerto 80 del contenedor y se publica en el host (80 prod vía proxy externo, 8080 test por defecto en compose).
- `backend`: FastAPI con Gunicorn/Uvicorn en `:8000` dentro de la red interna `app`.
- `db`: Postgres 16 con volumen persistente por entorno.
- Nginx del frontend hace proxy a `backend` en `/api/` (ver `frontend/nginx.conf.frontend`).

## Proxy TLS (Caddy) con WebSockets

Si publicas el stack detrás de un proxy global (recomendado para TLS), usa Caddy 2 y asegúrate de enrutar correctamente `/api` y `/socket.io` al backend.

Ejemplo de `Caddyfile` para producción (contenedor `caddy` en la red `proxy-global` con alias hacia los servicios):

```
marine.hsotrade.com {
  encode zstd gzip

  @api path /api/*
  reverse_proxy @api hsomarine-prod-backend:8000

  # Socket.IO (Engine.IO) necesita pasar WebSockets y long-polling
  @socket path /socket.io* /socket.io/*
  reverse_proxy @socket hsomarine-prod-backend:8000

  # Resto al frontend (Next.js standalone en :80)
  reverse_proxy hsomarine-prod-frontend:80
}
```

Notas importantes:

- Caddy 2 maneja WebSockets de forma automática en `reverse_proxy`, no hace falta headers manuales.
- Los contenedores `frontend` y `backend` ya exponen aliases en la red `proxy-global`:
  - Backend: `hsomarine-prod-backend:8000`
  - Frontend: `hsomarine-prod-frontend:80`
- En este proyecto, el cliente Socket.IO del frontend se conecta a la misma raíz (`window.location.origin`) con `path: "/socket.io"`. Por eso el proxy debe enviar ese path al backend.
- Para comprobar que el proxy está ruteando bien, abre en el navegador:
  - `https://marine.hsotrade.com/api/healthz` → debe responder `{ "status": "ok" }`.
  - `https://marine.hsotrade.com/socket.io/?EIO=4&transport=polling` → debe devolver un paquete de handshake (status 200) con un JSON tipo `{"sid":...,"upgrades":["websocket"],...}`. Si ves 400/403, el path no está yendo al backend.

Recarga de Caddy (en Portainer o Docker):

- Monta el `Caddyfile` en `/etc/caddy/Caddyfile` dentro del contenedor `caddy`.
- Tras editarlo, recarga:

  ```bash
  docker exec -it hsomarine-proxy caddy reload --config /etc/caddy/Caddyfile
  ```

Si usas Traefik o Nginx, aplica el mismo principio: enruta `/api/*` y `/socket.io/*` al backend, el resto al frontend, y habilita WebSockets.

## Pasos en Portainer

1) Crear Stack de PRUEBAS

- En Portainer, Stacks > Add stack > Web editor.
- Pega el contenido de `docker-compose.test.yml`.
- En Variables de entorno del stack (o en el campo Env file):
  - Copia/pega el contenido de `variables.env.test` (revisa valores). Alternativamente sube un archivo `.env` con esos pares clave/valor.
- Deploy the stack.

2) Crear Stack de PRODUCCIÓN

- Repite el proceso con `docker-compose.prod.yml`.
- Usa las variables de `variables.env.production`.
- Asegúrate de que el puerto 80 del host esté libre si vas a publicar el frontend en 80 (o usa un proxy como Caddy/Traefik para TLS).

## Variables clave

- DB: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
- App: `JWT_SECRET_KEY`, `JWT_AUDIENCE`, `ALLOWED_HOSTS`, `CORS_ORIGINS`, `FRONTEND_URL`.
- Integraciones: `ODOO_*`, `PLAID_*`, `MS_TRANSLATOR_*`, `DUE_N8N_*`, SMTP.

Notas:
- En `CORS_ORIGINS` corrige URLs inválidas si las ves duplicadas (p.ej. `http://http://...`).
- El backend usa `ROOT_PATH` vacío porque Nginx ya publica `/api/` hacia el backend.
- La app crea tablas automáticamente al iniciar. Puedes ejecutar seeds/usuarios usando el CLI si fuese necesario.
- Si necesitas exponer la DB a una IP concreta, edita el mapeo de puertos (5432) en el compose o usa túnel SSH.

## Semillas y usuario admin (opcional)

Si necesitas crear un superadmin o asegurar permisos/planes:

1. Abre una consola en el contenedor `backend` desde Portainer.
2. Ejecuta:

```bash
python -m app.manage seed-all
python -m app.manage create-superuser --email admin@example.com --password 'CambiaEsto!'
```

## Healthchecks y verificación

- Backend health: `GET http://<host>/api/healthz` debe responder `{"status":"ok"}`.
- Métricas: `GET http://<host>/api/metrics`.
- Logs: revisa `backend` y `db` desde la vista de contenedores de Portainer.

## Actualizaciones

- Para publicar una nueva versión, usa "Recreate" del servicio `frontend` o `backend` después de que Portainer reconstruya las imágenes (si usas build dentro del stack) o apunta a imágenes preconstruidas en un registry.

## Alternativa con imágenes preconstruidas

Si prefieres no compilar en Portainer, construye y sube imágenes a un registry (Docker Hub, GHCR) y reemplaza los bloques `build:` por `image: <tu-registry>/<nombre>:<tag>` en ambos compose.
