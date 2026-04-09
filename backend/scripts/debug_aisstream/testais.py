import asyncio
import websockets
import json

async def buscar_barco_por_mmsi(mmsi):
    # URL del stream de AIS [1]
    url = "wss://stream.aisstream.io/v0/stream"
    
    async with websockets.connect(url) as websocket:
        # Mensaje de suscripción con tu API Key y el filtro MMSI [4]
        # Se requiere enviar este mensaje antes de 3 segundos tras conectar [5, 6]
        subscribe_message = {
            "APIKey": "a39fb3e8e0feae4d5c6f06b4d96802d3d3ae1c1c",
            "BoundingBoxes": [[[-90, -180], [90, 180]]], # Área de búsqueda global [1, 2]
            "FiltersShipMMSI": [str(mmsi)] # El MMSI debe ser una lista de strings [2, 4]
        }

        # Enviamos la solicitud de suscripción en formato JSON
        await websocket.send(json.dumps(subscribe_message))

        print(f"Buscando datos para el MMSI: {mmsi}...")

        # Escuchamos los mensajes entrantes
        async for message in websocket:
            # Los mensajes se reciben en formato JSON [7]
            data = json.loads(message)
            
            # Cada mensaje contiene MetaData, MessageType y el Message con los datos [4]
            tipo_mensaje = data.get("MessageType")
            metadata = data.get("MetaData")
            detalles_barco = data.get("Message")

            print(f"\nNuevo mensaje recibido: {tipo_mensaje}")
            print(f"Nombre del barco: {metadata.get('ShipName')}")
            print(f"Datos: {detalles_barco}")

# Ejemplo de uso: Reemplaza '244670316' por el MMSI que desees buscar
if __name__ == "__main__":
    mmsi_objetivo = "366081080" 
    try:
        asyncio.run(buscar_barco_por_mmsi(mmsi_objetivo))
    except KeyboardInterrupt:
        print("\nBúsqueda finalizada por el usuario.")