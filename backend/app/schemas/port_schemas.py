from pydantic import BaseModel
from typing import List, Optional

class PortListEntry(BaseModel):
    port_number: int
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class PortListResponse(BaseModel):
    ports: List[PortListEntry]

class PortDetailsResponse(BaseModel):
    # just return the model object directly in the route and let FastAPI serialize it.
    pass
