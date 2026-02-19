#!/usr/bin/env python3
"""
Script para verificar que el endpoint /details incluya el flag.
"""
import requests
import sys

def verify_details_api(mmsi):
    url = f"http://localhost:8000/details/{mmsi}"
    print(f"🚀 Probando endpoint: {url}")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("✅ Respuesta recibida (200 OK)")
            vessel_data = data.get("data", {})
            flag = vessel_data.get("flag")
            
            print(f"📊 MMSI: {data.get('mmsi')}")
            print(f"📊 Nombre: {vessel_data.get('ship_name')}")
            print(f"🚩 FLAG (Country): {flag}")
            
            if flag and flag != "N/A":
                print("🎉 ÉXITO: El campo 'flag' está presente y tiene un valor válido.")
            else:
                print("⚠️  AVISO: El campo 'flag' está presente pero es 'N/A' o nulo.")
        else:
            print(f"❌ ERROR: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error al conectar con el backend: {e}")

if __name__ == "__main__":
    # Usar un MMSI de prueba (ej: 710000001 - Brasil)
    test_mmsi = "257082000" # Noruega (mencionado en el plan)
    if len(sys.argv) > 1:
        test_mmsi = sys.argv[1]
    verify_details_api(test_mmsi)
