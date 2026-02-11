from pydantic import BaseModel
from typing import List, Optional

class PortListEntry(BaseModel):
    port_number: int
    lon: Optional[float] = None  # xcoord from DB
    lat: Optional[float] = None  # ycoord from DB

class PortListResponse(BaseModel):
    ports: List[PortListEntry]

class PortDetailsResponse(BaseModel):
    # just return the model object directly in the route and let FastAPI serialize it.
    pass
