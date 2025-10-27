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

@router.get("/aisstream/positions", response_class=JSONResponse)
def get_positions(service: AISBridgeService = Depends(get_ais_bridge_service)):
    if not service:
        return JSONResponse(content={"error": "AISBridgeService not running"}, status_code=503)
    return service.get_positions()
