"""
Script de diagnóstico para AISstream.
Muestra los primeros N mensajes RAW para verificar conectividad y formato de respuesta.
"""
import asyncio
import websockets
import json

API_KEY = "a39fb3e8e0feae4d5c6f06b4d96802d3d3ae1c1c"
MAX_MESSAGES = 5  # Cuántos mensajes mostrar antes de salir

async def diagnosticar():
    url = "wss://stream.aisstream.io/v0/stream"
    print(f"Conectando a {url}...")

    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=30) as websocket:
            print("✅ Conexión WebSocket establecida.\n")

            # Paso 1: Suscripción global (sin filtros de zona ni tipo)
            subscribe_message = {
                "APIKey": API_KEY,
                "BoundingBoxes": [[[-90, -180], [90, 180]]],  # Todo el mundo
                "FilterMessageTypes": ["PositionReport"]       # Solo posición para reducir volumen
            }

            await websocket.send(json.dumps(subscribe_message))
            print(f"📤 Suscripción enviada:\n{json.dumps(subscribe_message, indent=2)}\n")
            print(f"⏳ Esperando hasta {MAX_MESSAGES} mensajes...\n")

            count = 0
            async for message_json in websocket:
                data = json.loads(message_json)

                # Verificar error de API
                if "error" in data:
                    print(f"❌ ERROR DE API: {data['error']}")
                    print("   Verifica que tu API Key sea válida en https://aisstream.io")
                    return

                count += 1
                print(f"=== Mensaje {count} ===")
                print(f"MessageType: {data.get('MessageType')}")
                
                meta = data.get("MetaData", {})
                print(f"MetaData keys: {list(meta.keys())}")
                print(f"  MMSI: {meta.get('MMSI')}")
                print(f"  ShipName: {meta.get('ShipName')}")
                print(f"  latitude: {meta.get('latitude')}  (nota: minúscula)")
                print(f"  longitude: {meta.get('longitude')}  (nota: minúscula)")
                print(f"  time_utc: {meta.get('time_utc')}")
                print(f"Message keys: {list(data.get('Message', {}).keys())}")
                print()

                if count >= MAX_MESSAGES:
                    print(f"✅ Diagnóstico completado: {count} mensajes recibidos correctamente.")
                    print("   La API Key y la conexión funcionan bien.")
                    print("   Si venezuela.py no da resultados, es porque no hay barcos en esa zona ahora.")
                    break

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ Conexión cerrada: {e}")
        print("   Posible causa: API Key inválida, o no se envió la suscripción a tiempo (< 3 seg).")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(diagnosticar())
