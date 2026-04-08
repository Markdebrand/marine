import asyncio
import websockets
import json

async def rastrear_venezuela():
    url = "wss://stream.aisstream.io/v0/stream"
    
    async with websockets.connect(url) as websocket:
        # Configuración para las costas de Venezuela
        # Bounding Box: [[lat_min, lon_min], [lat_max, lon_max]]
        subscribe_message = {
            "APIKey": "a39fb3e8e0feae4d5c6f06b4d96802d3d3ae1c1c",
            "BoundingBoxes": [[[0.5, -73.5], [16.0, -59.5]]],
            # Filtramos tipos de mensajes para obtener datos de posición y estáticos (nombres, destinos)
            "FilterMessageTypes": ["PositionReport", "ShipStaticData", "StandardClassBPositionReport"]
        }

        await websocket.send(json.dumps(subscribe_message))

        print("Conectado. Esperando datos de barcos cerca de Venezuela...")

        async for message in websocket:
            data = json.loads(message)
            metadata = data.get("MetaData", {})
            message_type = data.get("MessageType")
            ship_details = data.get("Message", {})

            # Extraemos información general útil
            nombre = metadata.get("ShipName", "Desconocido")
            mmsi = metadata.get("MMSI")
            lat = metadata.get("Latitude")
            lon = metadata.get("Longitude")
            
            print(f"\n--- Barco Detectado: {nombre} (MMSI: {mmsi}) ---")
            print(f"Tipo de Mensaje: {message_type}")
            print(f"Posición: Lat {lat}, Lon {lon}")
            
            # Si el mensaje es de datos estáticos, podemos ver el destino
            if message_type == "ShipStaticData":
                destino = ship_details.get("Destination", "No disponible")
                print(f"Destino declarado: {destino}")

if __name__ == "__main__":
    try:
        asyncio.run(rastrear_venezuela())
    except KeyboardInterrupt:
        print("\nDeteniendo el rastreo.")