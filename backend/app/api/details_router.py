# details_router.py
from fastapi import APIRouter, Path, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Optional
import asyncio

router = APIRouter(prefix="/details", tags=["details"])
logger = logging.getLogger(__name__)

# Dependencia para obtener el servicio AISBridge
def get_ais_bridge_service():
    from app.main import app
    return getattr(app.state, "ais_bridge", None)

@router.get("/{mmsi}", response_class=JSONResponse)
async def get_ship_details(
    mmsi: str = Path(..., description="MMSI del barco"),
    service = Depends(get_ais_bridge_service)
):
    print(f"=== SOLICITANDO DETALLES PARA MMSI: {mmsi} ===")
    
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Servicio AIS no disponible"
        )

    # Validar MMSI
    if not mmsi.isdigit() or len(mmsi) != 9:
        raise HTTPException(
            status_code=400,
            detail="MMSI debe ser un número de 9 dígitos"
        )

    try:
        # Usar el servicio existente para obtener datos estáticos
        ship_data = await service.get_ship_static_data(mmsi, timeout=30.0)
        print(f"Resultado del servicio: {ship_data}")
        
        if ship_data:
            return {
                "mmsi": mmsi,
                "data": ship_data,
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron datos estáticos para el barco. El barco puede no estar transmitiendo datos estáticos en este momento."
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Timeout: No se recibieron datos del barco en el tiempo esperado"
        )
    except Exception as e:
        logger.error(f"Error obteniendo datos del barco: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )