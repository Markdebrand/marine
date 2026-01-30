# HSO Marine - Documentación del Proyecto

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Backend](#backend)
    - [AIS Stream Integration](#ais-stream-integration)
    - [Sistema de Autenticación Avanzado](#sistema-de-autenticación)
    - [Integración con Odoo (ERP)](#integración-con-odoo)
4. [Frontend](#frontend)
    - [Visualización de Mapa](#visualización-de-mapa)
    - [Gestión de Estado y Suscripciones](#gestión-de-estado-y-suscripciones)
5. [Flujo de Datos](#flujo-de-datos)
6. [Base de Datos](#base-de-datos)
7. [Despliegue](#despliegue)

---

## 🎯 Visión General

**HSO Marine** es una aplicación web de seguimiento de embarcaciones en tiempo real que utiliza datos AIS (Automatic Identification System) para visualizar la posición de barcos en un mapa interactivo.

### Tecnologías Principales

- **Backend**: FastAPI (Python 3.12)
- **Frontend**: Next.js 16 + TypeScript + React 19
- **Base de Datos**: PostgreSQL + SQLAlchemy 2.0
- **Caché/Service Coordination**: Redis
- **Mapas**: MapLibre GL
- **Comunicación**: Socket.IO + WebSockets

---

## 🏗️ Arquitectura del Sistema

El proyecto sigue una arquitectura de microservicios desacoplados:

- **Backend**: Actúa como puente entre AIS Stream, Odoo y los clientes web. Gestiona la lógica de autenticación, persistencia y procesamiento en tiempo real.
- **Frontend**: SPA optimizada para el renderizado masivo de datos geográficos.

---

## 🔧 Backend

### 1. Integración AIS y Búsqueda de Barcos

El `AISBridgeService` gestiona la conexión con AIS Stream y mantiene un estado en memoria de las posiciones.

#### **Búsqueda de Embarcaciones** (`app/api/details_router.py`)
El sistema permite buscar barcos por **MMSI** o **Nombre**:
1. **MMSI Directo**: Si la consulta son 9 dígitos, busca directamente en el `AISBridgeService`.
2. **Búsqueda por Nombre**: Si no es un MMSI, busca en la tabla `marine_vessel` usando `ilike`.
3. **Fallback a DB**: Si el barco no está en el stream actual de memoria, se recuperan los últimos datos conocidos de la base de datos.
4. **Enriquecimiento**: Si se encuentra en DB pero el servicio tiene una posición reciente, se combinan los datos.

### 2. Sistema de Autenticación (`app/auth/`)

Un sistema robusto que va más allá del JWT básico:

- **Master Token**: Existe un `MASTER_TOKEN` configurable que otorga privilegios de superadmin virtual, saltando las comprobaciones de sesión normales. Útil para integraciones administrativas externas.
- **Single Session Policy**: Configurable (`block` o `force`). Evita que un mismo usuario tenga múltiples sesiones activas simultáneamente.
- **Static Auth**: Permite un login rápido en entornos de desarrollo usando credenciales estáticas configuradas en `.env`.
- **Session Heartbeat**: Endpoint `/auth/ping` y middleware que actualizan `last_seen_at` para rastrear la actividad real del usuario.
- **Setup Password Flow**: Cuando un admin crea un usuario, se genera un token de larga duración (7 días) para que el usuario configure su contraseña inicial.

### 3. Integración con Odoo (`app/integrations/odoo/`)

Conexión bidireccional con el ERP de HSO Trade:

- **Odoo Service**: Cliente XML-RPC que maneja perfiles (Default, Staging, ERP). permite listar clientes reales, leads y oportunidades de negocio.
- **Gestión de Facturas**: Endpoint `/invoices` que consulta en tiempo real las facturas de Odoo asociadas al email del usuario.
- **Confirmación de Clientes**: Un webhook `/odoo/customer-confirmed` recibe actualizaciones de Odoo (firmadas con HMAC) para crear automáticamente cuentas de usuario en Marine, asignarles un plan y generar un token de activación.

---

## 🎨 Frontend

### Visualización del Mapa (`AisLiveMap.tsx`)

- **Rendering**: Uso de GeoJSON con clustering para manejar >5000 barcos sin pérdida de rendimiento.
- **Optimización**: Viewport culling (solo se procesa lo visible) y muestreo estable para limitar el número de símbolos dibujados.
- **Persistencia**: Los datos de los barcos se guardan en `localStorage` cada 2 segundos para permitir una carga instantánea al recargar la página.

### Suscripciones y Navegación

- **Gating**: Los componentes verifican el `subscription_status` contenido en el payload del JWT.
- **Redirección Inteligente**: Si un usuario tiene una suscripción inactiva, el frontend lo redirige automáticamente a la sección de pagos/perfil.
- **Zustand Store**: Gestión centralizada del estado del mapa (centro, zoom) y de la sesión del usuario.

---

## 🔄 Flujo de Datos

### Ciclo de Vida del Usuario (Odoo -> Marine)
1. **Venta en Odoo**: El comercial confirma un pedido.
2. **Webhook**: Odoo dispara un POST a Marine con los datos del cliente y el plan.
3. **Provisión**: Marine crea el usuario inactivado y genera un link de activación.
4. **Activación**: El usuario recibe el email, configura su contraseña y entra al sistema.

---

## 💾 Base de Datos

### Modelos Principales
- `User`: Datos de cuenta, roles (`user`, `admin`, `superadmin`) y metadatos de Odoo.
- `SessionToken`: Registro de cada dispositivo/navegador activo con `user_agent` e `ip`.
- `Subscription` & `Plan`: Controlan el acceso a las funcionalidades según el nivel de pago.
- `MarineVessel`: Base de datos de referencia para búsqueda por nombre y datos estáticos de barcos.

---

## 🚀 Despliegue

El proyecto está diseñado para ejecutarse en contenedores Docker:

- **docker-compose.prod.yml**: Configuración para entornos de alto rendimiento con reinicio automático.
- **docker-compose.test.yml**: Entorno de desarrollo con hot-reload para backend y frontend.
- **Gunicorn**: El backend utiliza Gunicorn como manager de procesos Uvicorn para mayor estabilidad en producción.

---

**Última actualización**: 2026-01-30
