# details_router.py
from fastapi import APIRouter, Path, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Optional
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.database import get_db
from app.db.models.marine_vessel import MarineVessel
from app.db.models.marine_country import MarineCountry
from app.schemas.vessel_schemas import VesselDetailsWrapper, VesselData, VesselDimensions

router = APIRouter(prefix="/details", tags=["details"])
logger = logging.getLogger(__name__)

# Dependencia para obtener el servicio AISBridge
def get_ais_bridge_service():
    from app.main import app
    return getattr(app.state, "ais_bridge", None)

def parse_timestamp(ts_val) -> str:
    """
    Intenta parsear un timestamp en varios formatos y devolver ISO 8601 string.
    Si falla o es nulo, devuelve la fecha actual en UTC.
    """
    if not ts_val:
        return datetime.now(timezone.utc).isoformat()
    
    if isinstance(ts_val, datetime):
        return ts_val.isoformat()
    
    ts_str = str(ts_val).strip()
    if not ts_str:
        return datetime.now(timezone.utc).isoformat()
        
    # Intentar formatos comunes
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO con timezone
        "%Y-%m-%dT%H:%M:%S%z",     # ISO sin microsegundos
        "%Y-%m-%d %H:%M:%S%z",     # Espacio en vez de T
        "%Y-%m-%d %H:%M:%S",       # Sin timezone (asumir UTC)
        "%Y-%m-%dT%H:%M:%S",       # ISO naive
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(ts_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
            
    # Si todo falla, devolver el string original o datetime actual como fallback seguro
    # Preferimos devolver algo parseable por JS si es posible, pero si es basura,
    # el frontend tendrá que lidiar con ello o mostrar 'Invalid Date'.
    # Retornamos el original por si acaso es un formato que JS sí entiende nativamente.
    return ts_str

@router.get("/{query}", response_model=VesselDetailsWrapper)
async def get_ship_details(
    query: str = Path(..., description="MMSI o nombre del barco"),
    service = Depends(get_ais_bridge_service),
    db: Session = Depends(get_db)
):
    print(f"=== SOLICITANDO DETALLES PARA QUERY: {query} ===")
    
    mmsi = None
    
    # Intentar tratar query como MMSI si son 9 dígitos
    if query.isdigit() and len(query) == 9:
        mmsi = query
    else:
        # Buscar por nombre en la base de datos
        logger.info(f"Buscando barco por nombre: {query}")
        vessel = db.execute(
            select(MarineVessel).where(MarineVessel.name.ilike(f"%{query}%"))
        ).first()
        
        if vessel:
            vessel = vessel[0] # SQLAlchemy result proxy returns tuples when using select(Model) in some versions or depending on execution
            mmsi = vessel.mmsi
            logger.info(f"Nombre '{query}' resuelto a MMSI: {mmsi}")
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró ningún barco con el nombre o MMSI: {query}"
            )

    if not service:
        # Si el servicio no está disponible (ej: configuración) igual intentamos DB
        pass

    # Validar que tenemos un MMSI válido (ya sea directo o resuelto)
    if not mmsi or not mmsi.isdigit() or len(mmsi) != 9:
        raise HTTPException(
            status_code=400,
            detail="MMSI inválido o no se pudo resolver el nombre"
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

    # Obtener nombre del país (flag) basado en los primeros 3 dígitos del MMSI
    country_name = "N/A"
    try:
        mid = int(mmsi[:3])
        country = db.execute(
            select(MarineCountry).where(MarineCountry.mid == mid)
        ).scalar_one_or_none()
        if country:
            country_name = country.country
    except (ValueError, TypeError):
        pass

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
                flag=country_name,
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
                timestamp=parse_timestamp(realtime_data.get('timestamp')),
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
            flag=country_name,
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
            timestamp=parse_timestamp(ext_refs.get('timestamp') or vessel.updated_at),
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