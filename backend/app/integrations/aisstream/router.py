# router.py
"""
Router para exponer posiciones AIS actuales vía API REST.
"""
from fastapi import APIRouter, Depends
from app.integrations.aisstream.service import AISBridgeService
from fastapi.responses import JSONResponse

router = APIRouter()

# Dependencia para obtener instancia del servicio (ajustar según DI real)
def get_ais_bridge_service():
    from app.main import app
    return getattr(app.state, "ais_bridge", None)


# Endpoint compatible con el frontend: /api/ais/positions
@router.get("/api/ais/positions", response_class=JSONResponse)
def get_positions_api(service: AISBridgeService = Depends(get_ais_bridge_service)):
    if not service:
        return JSONResponse(content={"error": "AISBridgeService not running"}, status_code=503)
    # Formato esperado: lista de dicts {id, lon, lat, ...}
    ships = []
    for ship_id, positions in getattr(service, '_ships', {}).items():
        if positions:
            lat, lon = positions[-1]
            ships.append({
                "id": ship_id,
                "lat": lat,
                "lon": lon,
                # Puedes agregar más campos si los tienes disponibles
            })
    return ships
