# Diagramas de Flujo - HSOMarine (Mermaid)

Este documento contiene el código Mermaid para visualizar cada uno de los procesos del sistema.

## 1. Ingesta de Datos AIS
```mermaid
flowchart TD
    Start([Inicio]) --> Config[Cargar Configuración y API Key]
    Config --> Connect[Conectar a AISStream WebSockets]
    Connect --> Receive{Recibir Mensaje}
    Receive --> Dynamic{¿Dato Dinámico/Posición?}
    Dynamic -- Sí --> RedisBuffer[Almacenar en Buffer Redis]
    RedisBuffer --> SocketIO[Enviar a Clientes vía Socket.IO]
    Dynamic -- No --> Static{¿Dato Estático/Vessel?}
    Static -- Sí --> Clean[Limpiar y Validar Datos]
    Clean --> BufferPG[Buffer en Redis para Sincronización]
    BufferPG --> SyncLoop[Bucle de Sincronización]
    SyncLoop --> UpsertPG[(Upsert en PostgreSQL)]
    Static -- No --> Receive
    SocketIO --> Receive
    UpsertPG --> Receive
```

## 2. Visualización y API
```mermaid
flowchart TD
    Start([Inicio]) --> Access[Usuario Accede a Mapa]
    Access --> InitialFetch[Carga Inicial REST - Barcos cercanos]
    InitialFetch --> Render[Renderizado Inicial en MapLibre]
    Render --> SubSocket[Suscripción a Socket.IO]
    SubSocket --> ReceiveUpdate[Recibir Actualización de Posición]
    ReceiveUpdate --> UpdateIcon[Mover Ícono en Mapa]
    UpdateIcon --> Interaction{Interacción de Usuario}
    Interaction -- Click/Search --> FetchDetail[Consultar Detalles - MMSI MEM / Nombre DB]
    FetchDetail --> ShowPanel[Mostrar Panel de Información]
    ShowPanel --> ReceiveUpdate
```

## 3. Autenticación y Sesiones
```mermaid
flowchart TD
    Start([Inicio]) --> Input[Ingreso de Credenciales/Token]
    Input --> Validate{Validación de Credenciales}
    Validate -- Inválido --> Error[Mostrar Error de Autenticación]
    Validate -- Válido --> Master{¿Master Token?}
    Master -- Sí --> Superadmin[Otorgar Privilegios Superadmin]
    Master -- No --> SessionCheck{Política Sesión Única}
    SessionCheck -- Conflicto --> Policy[Forzar/Bloquear según Config]
    SessionCheck -- OK --> IssueJWT[Generar Token JWT]
    Policy --> IssueJWT
    Superadmin --> IssueJWT
    IssueJWT --> Heartbeat[Iniciar Heartbeat de Sesión]
    Heartbeat --> APIAccess([Acceso Concedido a API])
```

## 4. Integración Odoo
```mermaid
flowchart TD
    Start([Inicio]) --> OdooEvent[Evento en Odoo - Pago/Venta]
    OdooEvent --> Webhook[Disparar Webhook a Marine]
    Webhook --> HMAC{Validar Firma HMAC}
    HMAC -- Inválido --> LogError[Registrar Error y Descartar]
    HMAC -- Válido --> Process[Procesar Datos de Cliente]
    Process --> Lookup{¿Usuario Existe?}
    Lookup -- No --> CreateUser[Crear Usuario Inactivo]
    Lookup -- Sí --> UpdatePlan[Actualizar Plan y Suscripción]
    CreateUser --> MapPlan[Mapear Plan de Odoo a Marine]
    MapPlan --> Activation[Generar Token y Enviar Email]
    UpdatePlan --> End([Fin])
    Activation --> End
```

## 5. Tareas de Mantenimiento
```mermaid
flowchart TD
    Start([Inicio]) --> RunScript[Ejecución de Script - CLI/Cron]
    RunScript --> ConnectDB[Conexión a Base de Datos PG]
    ConnectDB --> TaskType{Tipo de Tarea}
    TaskType -- Banderas --> FlagUpdate[Iterar Barcos y Actualizar País via MMSI]
    TaskType -- Migración --> Alembic[Ejecutar Alembic Upgrade Head]
    TaskType -- Purga --> TokenPurge[Eliminar Tokens de Sesión Expirados]
    FlagUpdate --> Log[Registrar Resultados en Consola/Logs]
    Alembic --> Log
    TokenPurge --> Log
    Log --> End([Fin])
```
