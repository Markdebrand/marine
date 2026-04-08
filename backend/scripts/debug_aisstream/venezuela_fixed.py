import asyncio
import websockets
import json

async def rastrear_venezuela():
    url = "wss://stream.aisstream.io/v0/stream"
    
    async with websockets.connect(url) as websocket:
        # Bounding Box Venezuela: [[lat_min, lon_min], [lat_max, lon_max]]
        # Ampliado un poco para capturar más tráfico (incluye mar Caribe cercano)
        subscribe_message = {
            "APIKey": "a39fb3e8e0feae4d5c6f06b4d96802d3d3ae1c1c",
            "BoundingBoxes": [[[0.5, -73.5], [16.0, -59.5]]],
            "FilterMessageTypes": ["PositionReport", "ShipStaticData", "StandardClassBPositionReport"]
        }

        await websocket.send(json.dumps(subscribe_message))
        print("Conectado. Esperando datos de barcos cerca de Venezuela...")
        print("(Si no hay datos, puede que no haya barcos activos en la zona ahora mismo)\n")

        async for message_json in websocket:
            data = json.loads(message_json)

            # IMPORTANTE: verificar si la API devolvió un error
            if "error" in data:
                print(f"⚠️  Error de la API: {data['error']}")
                break

            message_type = data.get("MessageType")
            # MetaData tiene: MMSI, ShipName, latitude (minúscula), longitude (minúscula), time_utc
            metadata = data.get("MetaData", {})
            message_content = data.get("Message", {})

            nombre = metadata.get("ShipName", "Desconocido")
            mmsi = metadata.get("MMSI")
            lat = metadata.get("latitude")   # ← minúscula (corrección clave)
            lon = metadata.get("longitude")  # ← minúscula (corrección clave)
            time_utc = metadata.get("time_utc", "")

            print(f"\n--- Barco Detectado: {nombre} (MMSI: {mmsi}) ---")
            print(f"Tipo de Mensaje: {message_type}")
            print(f"Posición: Lat {lat}, Lon {lon}")
            print(f"Hora UTC: {time_utc}")

            # Para ShipStaticData, el destino está dentro de message_content["ShipStaticData"]
            if message_type == "ShipStaticData":
                ship_static = message_content.get("ShipStaticData", {})
                destino = ship_static.get("Destination", "No disponible")
                print(f"Destino declarado: {destino}")

if __name__ == "__main__":
    try:
        asyncio.run(rastrear_venezuela())
    except KeyboardInterrupt:
        print("\nDeteniendo el rastreo.")
