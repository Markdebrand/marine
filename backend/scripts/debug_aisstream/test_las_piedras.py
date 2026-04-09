import asyncio
import websockets
import json

API_KEY = "a39fb3e8e0feae4d5c6f06b4d96802d3d3ae1c1c"

async def test_las_piedras():
    url = "wss://stream.aisstream.io/v0/stream"
    print(f"Conectando a {url}...")

    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=30) as websocket:
            print("✅ Conexión WebSocket establecida.\n")

            # Bounding box para Las Piedras (Punto Fijo, Venezuela)
            # Aprox Lat 11.7, Lon -70.2
            subscribe_message = {
                "APIKey": API_KEY,
                "BoundingBoxes": [[[11.2, -70.6], [12.2, -69.8]]],  # Un poco mas amplio para agarrar Aruba y Las Piedras
                "FilterMessageTypes": ["PositionReport", "StandardClassBPositionReport"]
            }

            await websocket.send(json.dumps(subscribe_message))
            print(f"📤 Suscripción enviada:\n{json.dumps(subscribe_message, indent=2)}\n")
            print("⏳ Esperando mensajes...\n")

            count = 0
            async for message_json in websocket:
                data = json.loads(message_json)

                if "error" in data:
                    print(f"❌ ERROR DE API: {data['error']}")
                    return

                count += 1
                meta = data.get("MetaData", {})
                lat = meta.get('latitude')
                lon = meta.get('longitude')
                print(f"=== Mensaje {count}: MMSI {meta.get('MMSI')} ===")
                print(f"  ShipName: {meta.get('ShipName')}")
                print(f"  latitude: {lat}")
                print(f"  longitude: {lon}")
                print(f"  time_utc: {meta.get('time_utc')}")
                print()

                if count >= 10:
                    break

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_las_piedras())
