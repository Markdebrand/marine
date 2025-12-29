# details_router.py
from fastapi import APIRouter, Path, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Optional
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.database import get_db
from app.db.models.marine_vessel import MarineVessel
from app.schemas.vessel_schemas import VesselDetailsWrapper, VesselData, VesselDimensions

router = APIRouter(prefix="/details", tags=["details"])
logger = logging.getLogger(__name__)

# Dependencia para obtener el servicio AISBridge
def get_ais_bridge_service():
    from app.main import app
    return getattr(app.state, "ais_bridge", None)

@router.get("/{mmsi}", response_model=VesselDetailsWrapper)
async def get_ship_details(
    mmsi: str = Path(..., description="MMSI del barco"),
    service = Depends(get_ais_bridge_service),
    db: Session = Depends(get_db)
):
    print(f"=== SOLICITANDO DETALLES PARA MMSI: {mmsi} ===")
    
    if not service:
        # Si el servicio no está disponible (ej: configuración) igual intentamos DB
        pass

    # Validar MMSI
    if not mmsi.isdigit() or len(mmsi) != 9:
        raise HTTPException(
            status_code=400,
            detail="MMSI debe ser un número de 9 dígitos"
        )

    realtime_data = None
    if service:
        try:
            # Usar el servicio existente para obtener datos estáticos
            realtime_data = await service.get_ship_static_data(mmsi, timeout=2.0)
            print(f"Resultado del servicio: {realtime_data}")
        except asyncio.TimeoutError:
            logger.warning(f"Timeout obteniendo datos en tiempo real para MMSI {mmsi}, buscando en DB...")
        except Exception as e:
            logger.error(f"Error obteniendo datos del servicio: {str(e)}")

    if realtime_data:
        try:
            dims_data = realtime_data.get('dimensions', {})
            
            # Asegúrate de que estás convirtiendo tipos adecuadamente
            # Conversión de los campos que pueden ser de tipos inesperados
            vessel_data = VesselData(
                ship_name=realtime_data.get('ship_name', 'Unknown'),
                imo_number=str(realtime_data.get('imo_number')) if realtime_data.get('imo_number') is not None else None,
                call_sign=realtime_data.get('call_sign', 'N/A'),
                ship_type=realtime_data.get('ship_type', 'Unknown'),
                dimensions=VesselDimensions(
                    a=int(dims_data.get('a', 0)),  # Asegúrate de que estos son enteros
                    b=int(dims_data.get('b', 0)),
                    c=int(dims_data.get('c', 0)),
                    d=int(dims_data.get('d', 0)),
                    length=float(dims_data.get('length', 0)),  # Convertir a float
                    width=float(dims_data.get('width', 0))     # Convertir a float
                ),
                fix_type=str(realtime_data.get('fix_type', 'N/A')) if realtime_data.get('fix_type') is not None else 'N/A',
                eta=str(realtime_data.get('eta', 'N/A')),
                draught=str(realtime_data.get('draught', 'N/A')) if realtime_data.get('draught') is not None else 'N/A',
                destination=str(realtime_data.get('destination', 'N/A')),
                timestamp=str(realtime_data.get('timestamp', '')),
                latitude=None,
                longitude=None
            )

            # Intentar obtener posición (lat, lon)
            pos = service.get_ship_position(mmsi)
            if pos:
                vessel_data.latitude = pos[0]
                vessel_data.longitude = pos[1]
            
            return VesselDetailsWrapper(
                mmsi=mmsi,
                data=vessel_data,
                status="success"
            )
        except Exception as e:
            logger.error(f"Error mapeando datos realtime: {e}")
            # Si falla mapeo, fallback a DB

    # Fallback a DB
    logger.info(f"Buscando MMSI {mmsi} en base de datos...")
    vessel = db.execute(select(MarineVessel).where(MarineVessel.mmsi == mmsi)).scalar_one_or_none()
    
    if vessel:
        ext_refs = vessel.ext_refs or {}
        dims_data = ext_refs.get('dimensions', {})
        
        ts = ext_refs.get('timestamp') or vessel.updated_at.isoformat()
        
        vessel_data = VesselData(
            ship_name=vessel.name or "Unknown",
            imo_number=str(vessel.imo),  # Convertir a string
            call_sign=ext_refs.get('call_sign', 'N/A'),
            ship_type=vessel.type or "Unknown",
            dimensions=VesselDimensions(
                a=int(dims_data.get('a', 0)),  # Asegúrate que sean enteros
                b=int(dims_data.get('b', 0)),
                c=int(dims_data.get('c', 0)),
                d=int(dims_data.get('d', 0)),
                length=float(vessel.length or dims_data.get('length', 0)),  # Convertir a float
                width=float(vessel.width or dims_data.get('width', 0))      # Convertir a float
            ),
            fix_type=str(ext_refs.get('fix_type', 'N/A')) if ext_refs.get('fix_type') is not None else 'N/A',
            eta=ext_refs.get('eta', 'N/A'),
            draught=str(ext_refs.get('draught', 'N/A')) if ext_refs.get('draught') is not None else 'N/A',
            destination=ext_refs.get('destination', 'N/A'),
            timestamp=str(ts),
            latitude=None,
            longitude=None
        )
        
        # Intentar enriquecer con posición en tiempo real si el servicio está activo
        if service:
            pos = service.get_ship_position(mmsi)
            if pos:
                vessel_data.latitude = pos[0]
                vessel_data.longitude = pos[1]
        print(f"=== DETALLES PARA MMSI: {mmsi} DESDE LA BASE DE DATOS ===")
        print(vessel_data)
        return VesselDetailsWrapper(
            mmsi=mmsi,
            data=vessel_data,
            status="success (db-fallback)"
        )
        
    # Si no está en DB ni realtime
    raise HTTPException(
        status_code=404,
        detail="No se encontraron datos estáticos para el barco (ni en tiempo real ni en la base de datos)."
    )