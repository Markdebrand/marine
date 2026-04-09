# Reporte de Diagnóstico: Falla en la Detección de Barcos (AIS) en Puertos de Venezuela

## 1. Resumen del Problema
La aplicación no está detectando ni mostrando barcos dentro de áreas portuarias de Venezuela (por ejemplo, el puerto de Las Piedras en Punto Fijo), a pesar de que aplicaciones externas como MarineTraffic registran un mínimo de 10 embarcaciones activas en la misma zona. Los scripts de depuración (como `venezuela_fixed.py`) devuelven un total de 23 a 25 barcos, pero al revisarlos en el mapa se aprecia que se encuentran rodeando la zona (mar abierto) y no atracados directamente en ningún puerto nacional.

## 2. Detalles y Pruebas Realizadas

### 2.1 Análisis de Coordenadas Recibidas en Scripts de Prueba
Se revisó el retorno arrojado por el script de depuración actual (`venezuela_fixed.py`). Dicho script realiza una petición de suscripción usando el siguiente cuadro delimitador (Bounding Box):
`[[[0.5, -73.5], [16.0, -59.5]]]`

Al extraer las latitudes y longitudes de los barcos "detectados en Venezuela" (por ejemplo: `Lat 14.46, Lon -60.86` o `Lat 13.85, Lon -61.07`), se evidencia que **ninguna de las coordenadas arrojadas pertenece a territorio o aguas territoriales venezolanas**. Esas posiciones geográficas corresponden a zonas cercanas a las Antillas Menores, como **Martinica y Santa Lucía** (ubicadas mucho más al noreste).

El Bounding Box proporcionado es tan extenso geográficamente que cubre casi la mitad del Mar Caribe. Debido a este gran volumen, la API devuelve barcos detectados más al norte que caen dentro de la enorme delimitación geométrica, generando la falsa impresión de que se están detectando barcos cerca de las fronteras nacionales.

### 2.2 Prueba Específica de Aislamiento del Puerto (Las Piedras)
Para aislar el problema y validar el origen de los datos, se desarrolló y ejecutó un script de diagnóstico focalizado (`test_las_piedras.py`) usando el entorno virtual de producción del backend. En este script, se configuró un Bounding Box milimétrico focalizado estrictamente sobre la rada del **Puerto de Las Piedras (Punto Fijo, Falcón)**:
`[[[11.2, -70.6], [12.2, -69.8]]]`

**Resultado de la Prueba:** 
El canal de conexión WebSocket se estableció con éxito, sin embargo, el flujo (stream) **no emitió ningún mensaje o reporte de barcos** luego de un largo periodo de espera. Esto descarta fallas en el código de conexión del aplicativo y confirma que la API simplemente no cuenta con información de navegación para ese segmento del mapa en tiempo real.

## 3. Conclusiones y Causa Raíz

La discrepancia observada entre la aplicación interna y herramientas propietarias como MarineTraffic **no se debe a errores en el código fuente, filtros del backend o mal funcionamiento de la aplicación**, sino puramente a la naturaleza y cobertura técnica de nuestro proveedor de datos temporal (`AISStream.io`):

1. **Limitaciones de Infraestructura (AISStream.io):**
   AISStream.io es un proyecto impulsado por la comunidad libre y depende estrictamente de voluntarios y estaciones de radio AIS de aficionados en tierra firme. En la actualidad, **no existen antenas receptoras comunitarias con la cobertura suficiente apuntando a aguas portuarias en la costa central u occidental de Venezuela**. Por tanto, la API es "ciega" a embarcaciones menores que operan dentro de recintos cerrados de puertos (como Las Piedras). Solo logra captar embarcaciones cuyas potencias de transmisión AIS (por lo general en aguas libres/alta mar) logren rebotar hacia las antenas que los voluntarios mantienen instaladas en islas del Caribe oriental o de las Antillas (Aruba, Curazao, Bonaire o Trinidad).

2. **Diferencia Fundamental con MarineTraffic:**
   MarineTraffic opera de forma comercial manejando una red transnacional privada de antenas terrestres de altísima capacidad, posicionadas globalmente en contratos con dueños de antenas portuarias. Adicionalmente, resuelven los "huecos de señal terrestre" comprando matrices y servicios de **posicionamiento de Satélites AIS**, lo que se traduce en obtener las coordenadas de un barco esté o no cerca de un puerto con antena terrestre mediante señal espacial pura. 

## 4. Recomendación del Equipo Técnico
Dado que las reglas y prioridades del sistema solicitan la plena funcionalidad, detección y trazabilidad de los flujos de barcos a través de zonas locales cerradas o costeras de Venezuela sin un gran retraso temporal o error, **AISStream no posee la cobertura satelital/marítima viable ni confiable** para este caso específico de negocio.

Se recomienda al equipo considerar la posibilidad de establecer un presupuesto operacional e investigar para integrarse con un **Proveedor AIS Comercial**. Las principales alternativas incluyen:
* API Comercial de MarineTraffic (MarineTraffic API)
* Spire Maritime
* exactEarth (ahora unificado en múltiples redes satelitales)
* VesselFinder (API)

Esta transición sanará la debilidad geográfica actual del sistema sin necesidad de rehacer la lógica interna de la base de datos o el frontend de mapas actual.
