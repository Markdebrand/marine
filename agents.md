# HSO Marine - Documentación del Proyecto

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Backend](#backend)
4. [Frontend](#frontend)
5. [Flujo de Datos](#flujo-de-datos)
6. [Base de Datos](#base-de-datos)
7. [Integraciones Externas](#integraciones-externas)
8. [Despliegue](#despliegue)

---

## 🎯 Visión General

**HSO Marine** es una aplicación web de seguimiento de embarcaciones en tiempo real que utiliza datos AIS (Automatic Identification System) para visualizar la posición de barcos en un mapa interactivo.

### Tecnologías Principales

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 16 + TypeScript + React 19
- **Base de Datos**: PostgreSQL
- **Migraciones**: Alembic
- **Mapas**: MapLibre GL
- **Comunicación en Tiempo Real**: Socket.IO + WebSockets
- **Estado Global**: Zustand
- **Caché**: Redis

---

## 🏗️ Arquitectura del Sistema

El proyecto está dividido en dos partes principales:

```
marine/
├── backend/          # API REST + WebSocket Server
│   └── app/
│       ├── api/              # Endpoints REST
│       ├── auth/             # Autenticación y autorización
│       ├── core/             # Servicios centrales
│       ├── db/               # Modelos y migraciones
│       ├── integrations/     # Integraciones externas
│       │   └── aisstream/    # Cliente AIS Stream
│       └── main.py           # Punto de entrada
│
└── frontend/         # Aplicación Next.js
    └── src/
        └── app/
            └── (app)/
                └── map/      # Visualización del mapa
                    └── components/
                        └── ais/
                            └── AisLiveMap.tsx  # Componente principal del mapa
```

---

## 🔧 Backend

### Estructura del Backend

El backend está construido con **FastAPI** y sigue una arquitectura modular:

#### 1. **Punto de Entrada** (`app/main.py`)

El archivo `main.py` es el núcleo del backend y maneja:

- **Inicialización de FastAPI**: Configuración de la aplicación con CORS, middlewares y rutas
- **Socket.IO Server**: Servidor ASGI para comunicación en tiempo real
- **Gestión del Ciclo de Vida** (`lifespan`):
  - Inicialización de la base de datos
  - Creación del servicio AIS Bridge
  - Singleton lock con Redis para evitar múltiples conexiones WebSocket
  - Limpieza ordenada al apagar

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización
    setup_logging(LOG_LEVEL)
    sio_server = socketio.AsyncServer(...)
    init_db()
    
    # Iniciar AIS Bridge si está habilitado
    if AISSTREAM_ENABLED and AISSTREAM_API_KEY:
        bridge = AISBridgeService(sio_server, AISSTREAM_API_KEY)
        await bridge.start()
    
    yield
    
    # Limpieza
    if bridge:
        await bridge.stop()
```

#### 2. **Integración AIS Stream** (`app/integrations/aisstream/`)

Esta es la parte más importante del backend para el seguimiento de barcos:

##### **`aisstream_client.py`** (Versión Legacy)
- Cliente WebSocket básico que se conecta a `wss://stream.aisstream.io/v0/stream`
- Almacena posiciones en memoria con threading
- Mantiene historial de hasta 100 posiciones por barco

##### **`service.py`** (Versión Actual - AISBridgeService)

El servicio principal que gestiona la conexión con AIS Stream:

**Características principales:**

1. **Conexión WebSocket Persistente**:
   ```python
   async def _run(self):
       url = "wss://stream.aisstream.io/v0/stream"
       async with websockets.connect(url) as websocket:
           subscribe_message = {
               "APIKey": self.api_key,
               "BoundingBoxes": self.bounding_boxes,
               "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
           }
           await websocket.send(json.dumps(subscribe_message))
   ```

2. **Procesamiento de Mensajes**:
   - **PositionReport**: Actualiza posición (lat/lon) de los barcos
   - **ShipStaticData**: Almacena datos estáticos (nombre, tipo, dimensiones, destino, etc.)

3. **Emisión en Tiempo Real**:
   - Emite eventos Socket.IO cada 2 segundos con todas las posiciones actualizadas
   - Evento: `ais_position_batch` con array de posiciones

4. **Almacenamiento en Memoria**:
   ```python
   self._ships: Dict[str, List[List[float]]]  # Historial de posiciones
   self._last_pos: Dict[str, Tuple[float, float]]  # Última posición conocida
   self._ship_static_data: Dict[str, dict]  # Datos estáticos por MMSI
   ```

5. **Paginación y Filtrado**:
   ```python
   def get_positions_page(self, page, page_size, bbox):
       # Filtra por bounding box (west, south, east, north)
       # Retorna: {total, page, page_size, items: [{id, lat, lon}]}
   ```

##### **`router.py`**

Expone el endpoint REST para consultar posiciones:

```python
@router.get("/aisstream/positions")
def get_positions(
    page: int = 1,
    page_size: int = 1000,
    west: float | None = None,
    south: float | None = None,
    east: float | None = None,
    north: float | None = None,
):
    # Retorna posiciones paginadas con filtro opcional por bounding box
```

#### 3. **Sistema de Autenticación** (`app/auth/`)

Sistema completo de autenticación con:

- **JWT Tokens**: Access tokens + Refresh tokens
- **Gestión de Sesiones**: Tabla `SessionToken` en DB
- **Rate Limiting**: Protección contra fuerza bruta
- **Políticas de Sesión Única**: Configurable (block/force)
- **Endpoints**:
  - `POST /auth/login`: Autenticación
  - `POST /auth/register`: Registro de usuarios
  - `POST /auth/logout`: Cierre de sesión
  - `POST /auth/refresh`: Renovación de tokens
  - `GET /auth/me`: Perfil del usuario
  - `POST /auth/ping`: Heartbeat de sesión

#### 4. **Middlewares** (`app/core/middleware/`)

Cadena de middlewares en orden de ejecución:

1. **CORSMiddleware**: Manejo de CORS (más externo)
2. **AuditMiddleware**: Auditoría de requests
3. **RequireAuthMiddleware**: Protección de rutas
4. **AuthContextMiddleware**: Decodificación de JWT
5. **AppSwitchMiddleware**: Interruptor de disponibilidad
6. **RequestIdMiddleware**: Correlation ID
7. **GZipMiddleware**: Compresión
8. **ProxyHeadersMiddleware**: Headers de proxy
9. **TrustedHostMiddleware**: Validación de hosts (solo en producción)

#### 5. **Otros Routers** (`app/api/`)

- `details_router.py`: Detalles de embarcaciones
- `contact_router.py`: Gestión de contactos
- `support_router.py`: Soporte
- `system_router.py`: Estado del sistema
- `preferences_router.py`: Preferencias de usuario

---

## 🎨 Frontend

### Estructura del Frontend

El frontend está construido con **Next.js 16** y **TypeScript**:

```
frontend/src/app/
└── (app)/
    └── map/
        ├── page.tsx              # Página principal del mapa
        ├── components/
        │   └── ais/
        │       └── AisLiveMap.tsx  # Componente del mapa
        └── store/
            └── mapStore.ts       # Estado global con Zustand
```

### Componente Principal: `AisLiveMap.tsx`

Este es el componente más importante del frontend (964 líneas). Maneja:

#### 1. **Inicialización del Mapa**

```typescript
const map = new maplibregl.Map({
  container: mapEl.current!,
  style: {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
      }
    },
    layers: [{ id: "osm", type: "raster", source: "osm" }]
  },
  center: initialCenterRef.current,
  zoom: initialZoomRef.current,
});
```

#### 2. **Renderizado de Barcos con GeoJSON**

Utiliza una fuente GeoJSON con clustering para rendimiento:

```typescript
const sourceSpec = {
  type: "geojson",
  data: {
    type: "FeatureCollection",
    features: [],
  },
  cluster: true,
  clusterRadius: 60,
  clusterMaxZoom: 12,
};
```

**Capas del mapa:**

1. **`vessels-clusters`**: Clusters de barcos (icono + contador)
2. **`vessels-ship-symbol`**: Barcos individuales con rotación según COG (Course Over Ground)

#### 3. **Persistencia en LocalStorage**

```typescript
// Guardar barcos cada 2 segundos
useEffect(() => {
  const save = () => {
    const arr = Array.from(featuresRef.current.values());
    localStorage.setItem("ais_vessels", JSON.stringify(arr));
  };
  const interval = setInterval(save, 2000);
  return () => clearInterval(interval);
}, []);
```

#### 4. **Carga Inicial de Datos**

Carga paginada desde el endpoint REST:

```typescript
const PAGE_SIZE = 1000;
const MAX_ITEMS = 5000;
let page = 1;

while (received < MAX_ITEMS) {
  const res = await apiFetch(
    `/aisstream/positions?page=${page}&page_size=${PAGE_SIZE}` +
    `&west=${west}&south=${south}&east=${east}&north=${north}`
  );
  // Procesar items...
  page += 1;
}
```

#### 5. **Polling Periódico**

Actualiza posiciones cada 30 segundos:

```typescript
const pollPositions = async () => {
  const res = await apiFetch(
    `/aisstream/positions?page=1&page_size=2000` +
    `&west=${west}&south=${south}&east=${east}&north=${north}`
  );
  
  for (const item of res.items) {
    upsertFeature({
      mmsi: String(item.id),
      lon: item.lon,
      lat: item.lat,
    });
  }
  
  setVesselCount(featuresRef.current.size);
  setLastUpdate(new Date().toLocaleTimeString());
};

setInterval(pollPositions, 30000);
```

#### 6. **Optimización de Renderizado**

**Culling por Viewport:**
```typescript
const visible = all.filter((f) => {
  const [lon, lat] = f.geometry.coordinates;
  const inLat = lat >= south && lat <= north;
  const inLon = crossesAntimeridian
    ? lon >= west || lon <= east
    : lon >= west && lon <= east;
  return inLat && inLon;
});
```

**Muestreo Estable:**
```typescript
const MAX_RENDERED = 8000;
if (features.length > MAX_RENDERED) {
  const stride = Math.ceil(features.length / MAX_RENDERED);
  features = features.filter((f) => 
    stableHash(String(f.id)) % stride === 0
  );
}
```

#### 7. **Interactividad**

**Click en Barcos:**
```typescript
mapRef.current.on("click", LAYER_SHIP_SYMBOL_ID, async (e) => {
  const feature = features[0];
  const mmsi = feature.id;
  
  // Verificar caché
  const cached = vesselDetailsCache.current.get(mmsi);
  if (cached) {
    setSelectedVessel(cached);
    return;
  }
  
  // Fetch desde API
  const response = await apiFetch(`/details/${mmsi}`);
  vesselDetailsCache.current.set(mmsi, response);
  setSelectedVessel(response);
});
```

**Zoom en Clusters:**
```typescript
mapRef.current.on("click", LAYER_CLUSTERS_ID, (e) => {
  const clusterId = features[0].properties.cluster_id;
  source.getClusterExpansionZoom(clusterId, (err, zoomTo) => {
    map.easeTo({ center: [lng, lat], zoom: Math.min(zoomTo, 18) });
  });
});
```

#### 8. **Gestión de Estado con Zustand**

```typescript
const persistedCenter = useMapStore((s) => s.center);
const persistedZoom = useMapStore((s) => s.zoom);

// Guardar vista al mover el mapa
mapRef.current.on("moveend", () => {
  const c = mapRef.current.getCenter();
  const z = mapRef.current.getZoom();
  useMapStore.getState().setView([c.lng, c.lat], z);
});
```

### Dependencias del Frontend

```json
{
  "dependencies": {
    "next": "16.0.0",
    "react": "19.2.0",
    "react-dom": "19.2.0",
    "maplibre-gl": "5.9.0",
    "socket.io-client": "4.8.1",
    "zustand": "^5.0.8",
    "lucide-react": "^0.546.0"
  }
}
```

---

## 🔄 Flujo de Datos

### 1. Flujo de Datos AIS en Tiempo Real

```mermaid
graph LR
    A[AIS Stream API] -->|WebSocket| B[AISBridgeService]
    B -->|Store in Memory| C[_ships / _last_pos]
    B -->|Emit every 2s| D[Socket.IO Server]
    D -->|ais_position_batch| E[Frontend Clients]
    E -->|Update Map| F[MapLibre GL]
```

**Detalle del flujo:**

1. **AIS Stream → Backend**:
   - Conexión WebSocket persistente a `wss://stream.aisstream.io/v0/stream`
   - Recibe mensajes de tipo `PositionReport` y `ShipStaticData`
   - Almacena en memoria: `_ships`, `_last_pos`, `_ship_static_data`

2. **Backend → Frontend (Socket.IO)**:
   - Batch sender emite cada 2 segundos
   - Evento: `ais_position_batch`
   - Payload: `{positions: [{id, lat, lon}, ...]}`

3. **Frontend → Mapa**:
   - Actualiza `featuresRef.current` (Map de Features GeoJSON)
   - Flush throttled cada 400ms a la fuente GeoJSON
   - MapLibre re-renderiza automáticamente

### 2. Flujo de Datos REST (Polling)

```mermaid
graph LR
    A[Frontend] -->|GET /aisstream/positions| B[Backend Router]
    B -->|get_positions_page| C[AISBridgeService]
    C -->|Filter by bbox| D[_last_pos]
    D -->|Paginated Response| A
    A -->|Update Features| E[MapLibre GL]
```

**Detalle del flujo:**

1. **Carga Inicial**:
   - Frontend solicita múltiples páginas al cargar
   - Filtra por bounding box del viewport actual
   - Máximo 5000 items iniciales

2. **Polling Periódico** (cada 30 segundos):
   - Solicita primera página (2000 items)
   - Filtra por viewport actual
   - Actualiza posiciones existentes

3. **Refresh por Viewport**:
   - Debounced 800ms después de mover el mapa
   - Solicita primera página del nuevo viewport
   - Carga barcos visibles en la nueva área

### 3. Flujo de Autenticación

```mermaid
graph TD
    A[Usuario] -->|POST /auth/login| B[Auth Router]
    B -->|Verify Password| C[Database]
    C -->|User Valid| D[Generate JWT + Refresh Token]
    D -->|Store Session| E[SessionToken Table]
    E -->|Return Tokens| F[Frontend]
    F -->|Store in Memory| G[Auth Context]
    G -->|Include in Headers| H[Protected Requests]
```

---

## 💾 Base de Datos

### Tecnología

- **DBMS**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migraciones**: Alembic

### Uso Actual

> **Nota**: Actualmente la base de datos **no se usa para almacenar posiciones de barcos**. Los datos AIS se mantienen en memoria en el backend.

### Tablas Principales

1. **`users`**: Usuarios del sistema
   - Campos: `id`, `email`, `password_hash`, `role`, `is_superadmin`, `is_active`

2. **`session_tokens`**: Sesiones activas
   - Campos: `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `ip`, `user_agent`

3. **Otras tablas**:
   - `subscriptions`: Suscripciones de usuarios
   - `plans`: Planes de suscripción
   - `audit_logs`: Logs de auditoría
   - `contacts`: Contactos

### Migraciones con Alembic

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

Configuración en `backend/alembic.ini` y scripts en `backend/app/db/alembic/versions/`

---

## 🔌 Integraciones Externas

### 1. AIS Stream API

**URL**: `wss://stream.aisstream.io/v0/stream`

**Autenticación**: API Key (variable de entorno `AISSTREAM_API_KEY`)

**Tipos de Mensajes**:

1. **PositionReport**:
   ```json
   {
     "MessageType": "PositionReport",
     "Message": {
       "PositionReport": {
         "UserID": 123456789,
         "Latitude": 40.4168,
         "Longitude": -3.7038,
         "Cog": 180.5,
         "Sog": 12.3
       }
     }
   }
   ```

2. **ShipStaticData**:
   ```json
   {
     "MessageType": "ShipStaticData",
     "Message": {
       "ShipStaticData": {
         "UserID": 123456789,
         "Name": "VESSEL NAME",
         "CallSign": "ABC123",
         "ShipType": 70,
         "Dimension": {"A": 100, "B": 20, "C": 10, "D": 5},
         "Destination": "PORT NAME",
         "Eta": "11-19 12:00"
       }
     }
   }
   ```

**Filtros**:
- `BoundingBoxes`: Array de coordenadas `[[south-west], [north-east]]`
- `FilterMessageTypes`: Array de tipos de mensajes a recibir

### 2. Redis (Opcional)

**Uso**:
- **Socket.IO Client Manager**: Sincronización entre múltiples workers
- **Singleton Lock**: Garantiza una sola conexión WebSocket a AIS Stream
- **Caché**: Perfiles de usuario, rate limiting

**Configuración**:
```python
REDIS_URL = "redis://localhost:6379/0"
AISSTREAM_SINGLETON_LOCK_KEY = "aisstream:singleton_lock"
AISSTREAM_SINGLETON_LOCK_TTL = 300  # 5 minutos
```

---

## 🚀 Despliegue

### Estructura de Docker

El proyecto incluye archivos Docker Compose para diferentes entornos:

1. **`docker-compose.prod.yml`**: Producción
2. **`docker-compose.test.yml`**: Testing
3. **`docker-compose.proxy.yml`**: Proxy reverso

### Servicios Docker

**Backend**:
```dockerfile
# backend/Dockerfile.backend
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:asgi", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend**:
```dockerfile
# frontend/Dockerfile.frontend
FROM node:20
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Variables de Entorno

**Backend** (`.env`):
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/marine

# AIS Stream
AISSTREAM_ENABLED=true
AISSTREAM_API_KEY=your_api_key_here

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Auth
SINGLE_SESSION_POLICY=block  # o "force"
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOCKET_URL=http://localhost:8000
```

### Comandos de Despliegue

```bash
# Desarrollo
docker-compose -f docker-compose.test.yml up

# Producción
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Portainer

El proyecto incluye documentación para despliegue con Portainer:
- Ver `DEPLOY-PORTAINER.md` para instrucciones detalladas

---

## 📊 Rendimiento y Optimizaciones

### Backend

1. **Singleton Lock con Redis**: Evita múltiples conexiones WebSocket
2. **Batch Sending**: Agrupa posiciones cada 2 segundos
3. **Paginación**: Endpoints REST con paginación configurable
4. **Filtrado por Bounding Box**: Reduce datos transferidos
5. **Caché de Perfiles**: Redis cache para `/auth/me`

### Frontend

1. **GeoJSON Clustering**: Agrupa barcos cercanos en zoom bajo
2. **Viewport Culling**: Solo renderiza barcos visibles
3. **Muestreo Estable**: Limita a 8000 barcos renderizados
4. **Throttled Flush**: Actualiza mapa cada 400ms
5. **LocalStorage Persistence**: Guarda barcos para carga rápida
6. **Debounced Viewport Refresh**: Evita requests excesivos al mover mapa
7. **Caché de Detalles**: Almacena detalles de barcos consultados

---

## 🔐 Seguridad

### Backend

1. **JWT Authentication**: Tokens firmados con HS256
2. **Refresh Token Rotation**: Tokens de un solo uso
3. **Rate Limiting**: Protección contra fuerza bruta
4. **Session Management**: Control de sesiones activas
5. **CORS**: Configuración estricta de orígenes permitidos
6. **Middlewares de Seguridad**:
   - TrustedHostMiddleware
   - ProxyHeadersMiddleware
   - RequireAuthMiddleware

### Frontend

1. **HTTP-Only Cookies**: Tokens en cookies seguras (opcional)
2. **HTTPS Only**: En producción
3. **SameSite Cookies**: Protección CSRF
4. **Token Refresh**: Renovación automática antes de expiración

---

## 🧪 Testing

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm run lint
npm run build  # Verifica errores de TypeScript
```

---

## 📝 Notas Adicionales

### Limitaciones Actuales

1. **Sin Persistencia de Posiciones**: Los datos AIS solo están en memoria
2. **Sin WebSocket en Frontend**: Actualmente usa polling REST
3. **Caché Limitado**: LocalStorage tiene límite de ~5-10MB

### Mejoras Futuras Sugeridas

<!-- 1. **Implementar Socket.IO en Frontend**: Reemplazar polling por eventos en tiempo real -->
1. **Persistencia en DB**: Almacenar historial de posiciones
2. **Búsqueda de Barcos**: Endpoint para buscar por MMSI/nombre
3. **Rutas Históricas**: Visualizar trayectorias pasadas
4. **Notificaciones**: Alertas cuando barcos entran/salen de áreas
5. **Filtros Avanzados**: Por tipo de barco, bandera, etc.

---

## 🤝 Contribución

Para contribuir al proyecto:

1. Revisar esta documentación
2. Entender el flujo de datos AIS
3. Seguir las convenciones de código existentes
4. Crear migraciones para cambios en DB
5. Documentar nuevas funcionalidades

---

## 📚 Referencias

- [AIS Stream API Documentation](https://aisstream.io/documentation)
- [MapLibre GL Documentation](https://maplibre.org/maplibre-gl-js/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Socket.IO Documentation](https://socket.io/docs/v4/)

---

**Última actualización**: 2025-11-19
