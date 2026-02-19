from pydantic import BaseModel
from typing import Optional, Dict

class VesselDimensions(BaseModel):
    a: int = 0
    b: int = 0
    c: int = 0
    d: int = 0
    length: float = 0.0
    width: float = 0.0

class VesselData(BaseModel):
    ship_name: str
    imo_number: Optional[str] = None
    call_sign: str = "N/A"
    ship_type: str = "Unknown"
    flag: Optional[str] = "N/A"  # Added country name/flag
    dimensions: VesselDimensions
    fix_type: str = "N/A"
    eta: str = "N/A"
    draught: Optional[str] = "N/A"
    destination: str = "N/A"
    timestamp: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class VesselDetailsWrapper(BaseModel):
    mmsi: str
    data: VesselData
    status: str = "success"
