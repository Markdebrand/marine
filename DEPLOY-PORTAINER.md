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
