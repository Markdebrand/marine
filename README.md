# HSOMarine

**HSOMarine** es una plataforma avanzada de seguimiento de embarcaciones en tiempo real diseñada para proporcionar visibilidad completa sobre el tráfico marítimo global. Utiliza datos AIS (Automatic Identification System) procesados a través de una arquitectura moderna y escalable.

## 🚀 Características Principales

- **Seguimiento en Tiempo Real**: Visualización de miles de embarcaciones con actualizaciones constantes mediante WebSockets y Socket.IO.
- **Búsqueda Avanzada**: Localización de barcos por MMSI o nombre, con resolución inteligente y persistencia en base de datos.
- **Mapa Interactivo**: Basado en MapLibre GL con clustering de alto rendimiento y renderizado optimizado por GPU.
- **Integración con Odoo**: Sincronización automática de clientes, leads y facturación.
- **Gestión de Suscripciones**: Sistema robusto de planes (Basic, Pro, etc.) con control de acceso basado en roles.
- **Seguridad**: Autenticación JWT, rotación de tokens, políticas de sesión única y Master Token para administración.

## 🛠️ Stack Tecnológico

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, Zustand.
- **Backend**: FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic, PostgreSQL.
- **Infraestructura**: Docker, Redis (para caché y locks de servicios), Gunicorn/Uvicorn.
- **Datos**: Integración nativa con [AIS Stream](https://aisstream.io/).

## 🚦 Inicio Rápido

### Requisitos Previos

- Docker y Docker Compose
- Una API Key de AIS Stream

### Configuración

1. Clona el repositorio:
   ```bash
   git clone https://github.com/Markdebrand/marine.git
   cd marine
   ```

2. Configura las variables de entorno en `backend/.env` y `frontend/.env.local`.

3. Levanta los servicios con Docker:
   ```bash
   # Para desarrollo/test
   docker-compose -f docker-compose.test.yml up --build

   # Para producción
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 🏗️ Estructura del Proyecto

- `backend/`: API REST, WebSockets, lógica de negocio e integraciones.
- `frontend/`: Aplicación SPA moderna con visualización cartográfica.
- `docker/`: Configuraciones de contenedores y despliegue.

---

Para más detalles técnicos sobre la implementación y arquitectura, consulta [agents.md](agents.md).
