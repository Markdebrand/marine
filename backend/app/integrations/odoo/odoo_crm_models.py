from pydantic import BaseModel, EmailStr
from typing import Optional

class Client(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_id: Optional[list] = None
    activity_ids: Optional[list] = None
    country_id: Optional[list] = None
    company_name: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[list] = None
    zip: Optional[str] = None
    website: Optional[str] = None
    category_id: Optional[list] = None


class Lead(BaseModel):
    id: int
    name: str
    company_id: Optional[list] = None
    partner_id: Optional[list] = None
    email_from: Optional[str] = None
    phone: Optional[str] = None
    expected_revenue: Optional[float] = None
    probability: Optional[float] = None
    stage_id: Optional[list] = None