# router.py
"""
Router para exponer posiciones AIS actuales vía API REST.
"""
from fastapi import APIRouter, Depends, Query
from app.integrations.aisstream.service import AISBridgeService
from fastapi.responses import JSONResponse

router = APIRouter()

# Dependencia para obtener instancia del servicio (ajustar según DI real)
def get_ais_bridge_service():
    from app.main import app
    return getattr(app.state, "ais_bridge", None)

@router.get("/aisstream/positions", response_class=JSONResponse)
def get_positions(
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=5000),
    # Bounding box opcional: west,south,east,north (lon/lat)
    west: float | None = Query(None),
    south: float | None = Query(None),
    east: float | None = Query(None),
    north: float | None = Query(None),
    service: AISBridgeService = Depends(get_ais_bridge_service),
):
    if not service:
        return JSONResponse(content={"error": "AISBridgeService not running"}, status_code=503)
    bbox = None
    if all(v is not None for v in (west, south, east, north)):
        bbox = (west or 0.0, south or 0.0, east or 0.0, north or 0.0)
    result = service.get_positions_page(page=page, page_size=page_size, bbox=bbox)
    return JSONResponse(content=result)
