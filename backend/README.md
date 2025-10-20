# HSOMarine Backend (FastAPI)

Backend base en FastAPI reutilizable para proyectos HSOMarine. Incluye integración opcional con Odoo (XML-RPC), autenticación JWT, formularios de contacto vía SMTP y utilidades de observabilidad. Módulos activables por flags para adaptarlo a tu proyecto.

## Características
- Integración Odoo (opcional): endpoints `/odoo/*` y webhook de alta de cliente
- Autenticación JWT + Google OAuth (opcional)
- Formularios de contacto (SMTP) y soporte (opcional)
- Preferencias de usuario y releases (opcional)
- Observabilidad: `/metrics`, health, logging JSON opcional
- CORS listo para Next.js (localhost:3000 por defecto)
 - Soporte Socket.IO para reenvío AISStream en `/socket.io`

Performance / despliegue
- Singleton bridge: si configuras `REDIS_URL`, el bridge AISStream intentará tomar un lock en Redis (clave `AISSTREAM_SINGLETON_LOCK_KEY`) para evitar que múltiples workers abran conexiones al feed.
- Batching: puedes agrupar posiciones en el backend configurando `AISSTREAM_BATCH_MS` (ms) para emitir `ais_position_batch` con arrays de posiciones en lugar de eventos individuales.
- Filtros: usa `AISSTREAM_BOUNDING_BOXES` y `AISSTREAM_FILTER_MMSI` / `AISSTREAM_FILTER_TYPES` en `.env` para reducir el volumen de datos.


## Requisitos
- Python 3.10+
- (Opcional) Acceso a Odoo, si activas la integración

## Installation

1. **Clone the repository**

2. **Create and activate a virtual environment**
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate


3. **Instalar dependencias**
   pip install -r requirements.txt
 

4. **Variables de entorno**
   Crea un `.env` en la raíz con valores mínimos:
   ```env
   APP_NAME=HSOMarine API
   DEBUG=true
   FRONTEND_URL=http://localhost:3000
   CORS_ORIGINS=http://localhost:3000
   
   # Base de datos (Postgres recomendado)
   POSTGRES_HOST=127.0.0.1
   POSTGRES_PORT=5432
   POSTGRES_DB=hsomarine
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   
   # Flags de módulos
   ENABLE_ODOO_INTEGRATION=false
   ENABLE_GOOGLE_OAUTH=false
   ENABLE_CONTACT_FORMS=true
   ENABLE_SUPPORT_FORM=true
   ENABLE_RELEASES_API=true
   ENABLE_RPC_API=false
   
   # Odoo (si activas ENABLE_ODOO_INTEGRATION)
   ODOO_URL=https://your-odoo-server.com
   ODOO_DB=your_db_name
   ODOO_USER=your_user
   ODOO_PASSWORD=your_password
   ```

## Ejecutar el backend

Desde la raíz del backend:

```bash
uvicorn app.main:asgi --reload
```

API en `http://localhost:8000`. Documentación (`/docs`) visible cuando `DEBUG=true`.

## Endpoints principales

- `GET /healthz` → estado
- `GET /metrics` → Prometheus text
- Auth: `/auth/*`, Google OAuth: `/auth/google/*` (si habilitado)
- Odoo: `/odoo/*` (si habilitado)
- Contacto: `/contact/submit`, `/contact-us` (si habilitado)

## Notes
- Make sure your Odoo instance is accessible from the backend server.
- The backend normalizes data to avoid validation errors (e.g., converts `False` to `None` or `[]` as needed).
- For production, adjust CORS and security settings as required.

## Despliegue (Ubuntu + Nginx + Gunicorn)

1. System deps
   sudo apt update && sudo apt install -y python3 python3-venv python3-pip git nginx

2. Virtualenv
   python3 -m venv env && source env/bin/activate

3. Install
   pip install --upgrade pip && pip install -r requirements.txt gunicorn uvicorn

4. .env
   cp .env.example .env  # y rellena valores

5. Test locally
   gunicorn -c gunicorn.conf.py app.main:app

6. systemd (ejemplo)
   /etc/systemd/system/fastapi-backend.service
   [Unit]\nDescription=FastAPI backend\nAfter=network.target\n\n[Service]\nUser=www-data\nGroup=www-data\nWorkingDirectory=/ruta/a/backend\nEnvironmentFile=/ruta/a/backend/.env\nExecStart=/ruta/a/backend/env/bin/gunicorn -c /ruta/a/backend/gunicorn.conf.py app.main:app\n\n[Install]\nWantedBy=multi-user.target

7. Nginx (ejemplo)
   /etc/nginx/sites-available/fastapi-backend
   server {\n  listen 80;\n  server_name tu-dominio.com;\n  location / {\n    proxy_pass http://127.0.0.1:8000;\n    proxy_set_header Host $host;\n    proxy_set_header X-Real-IP $remote_addr;\n    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n    proxy_set_header X-Forwarded-Proto $scheme;\n  }\n}

8. Enable
   sudo ln -s /etc/nginx/sites-available/fastapi-backend /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx

9. TLS
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d tu-dominio.com

## Autenticación y sesiones

El backend emite JWT de acceso de corta duración y refresh tokens persistentes por dispositivo.

Endpoints:
- POST /auth/login { email, password } -> { access_token, token_type, refresh_token }
- POST /auth/refresh { refresh_token } -> { access_token, refresh_token }
- POST /auth/logout { refresh_token? }
- GET /auth/me
- GET /whoami (requiere Authorization: Bearer)
- GET /admin/ping (requiere rol admin)

Nota:
- El registro de usuarios está deshabilitado en esta versión (no existe `/auth/register`). El alta de usuarios se gestiona fuera del flujo público.

Seeding automático:
- Planes base (incluye "started").
- Usuario admin admin@example.com / Admin123! y organización "HSO Admin".

## Contacto (SMTP)

Las solicitudes del formulario de Contact Sales se envían por correo a `webform@hsomarine.com`, donde son ingeridas automáticamente por el CRM de Odoo. No se persisten en base de datos.

- Endpoint principal: `POST /contact/submit` (SMTP, respeta `EMAIL_TO`).
- Alternativa: `POST /contact-us` (router minimalista).

Variables de entorno relevantes (ejemplo):

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=support@hsomarine.com
SMTP_PASSWORD=********
SMTP_TLS=true
SMTP_SSL=false
EMAIL_SENDER=support@hsomarine.com
EMAIL_TO=webform@hsomarine.com
# Opcional: varias separadas por coma
SMTP_CC=ops@hsomarine.com, sales@hsomarine.com
```

Comportamiento:
- Remitente: `SMTP_USER`/`EMAIL_SENDER`.
- Destinatarios: `EMAIL_TO` (lista separada por comas).
- Se puede enviar acuse al remitente (si el adaptador lo permite); fallos en ese envío no bloquean la operación principal.

## Simulador AIS por Socket.IO

Se incluye un simulador que emite cada ~5s una lista de barcos falsos a todos los clientes Socket.IO conectados.

- Ruta Socket.IO: `/socket.io`
- Evento: `ais_update`
- Payload:
   - `vessels`: array de objetos `{ id, lat, lon, heading, speed }`

Uso en React con `socket.io-client`:

```ts
import { io } from 'socket.io-client';

const socket = io('http://localhost:8000', { path: '/socket.io' });

socket.on('ais_update', (data) => {
   console.log('AIS update', data.vessels.length);
});
```

Notas:
- Ajusta CORS en `.env` con `CORS_ORIGINS` si conectas desde otro dominio/puerto.
-- Si usas simulador local, sus parámetros estaban en `app/realtime/ais_simulator.py` (ahora eliminada). El flujo por defecto usa AISStream.