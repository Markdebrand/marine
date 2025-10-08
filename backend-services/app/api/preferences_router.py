from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any, Optional
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import UserPreference, User
from app.core.auth.session_manager import get_current_user

router = APIRouter(prefix="/preferences", tags=["preferences"])

MAX_FEATURED = 3
FEATURED_KEY = "market_featured"

class MarketFeaturedIn(BaseModel):
    items: List[str] = Field(default_factory=list, max_length=MAX_FEATURED)

class MarketFeaturedOut(BaseModel):
    items: List[str]
    updated_at: Optional[str] = None

@router.get("/market-featured", response_model=MarketFeaturedOut)
def get_market_featured(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user.id, UserPreference.key == FEATURED_KEY).first()
    if not pref:
        return MarketFeaturedOut(items=[])
    value = pref.value or {}
    items = value.get("items") if isinstance(value, dict) else []
    if not isinstance(items, list):
        items = []
    upd = getattr(pref, "updated_at", None)
    return MarketFeaturedOut(items=[str(i) for i in items][:MAX_FEATURED], updated_at=str(upd) if upd else None)

@router.put("/market-featured", response_model=MarketFeaturedOut)
def put_market_featured(payload: MarketFeaturedIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if len(payload.items) > MAX_FEATURED:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_FEATURED} items allowed")
    # normalizar keys (lower)
    norm = []
    seen = set()
    for k in payload.items:
        k2 = str(k).strip().lower()
        if k2 and k2 not in seen:
            norm.append(k2)
            seen.add(k2)
        if len(norm) >= MAX_FEATURED:
            break
    pref = db.query(UserPreference).filter(UserPreference.user_id == user.id, UserPreference.key == FEATURED_KEY).first()
    if not pref:
        pref = UserPreference(user_id=user.id, key=FEATURED_KEY, value={"items": norm})
        db.add(pref)
    else:
        # ensure it's a plain dict (SQLAlchemy JSON column will handle serialization)
        pref.value = {"items": list(norm)}  # type: ignore[assignment]
    db.commit()
    db.refresh(pref)
    upd = getattr(pref, "updated_at", None)
    return MarketFeaturedOut(items=norm, updated_at=str(upd) if upd else None)

@router.delete("/market-featured", response_model=MarketFeaturedOut)
def delete_market_featured(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user.id, UserPreference.key == FEATURED_KEY).first()
    if pref:
        db.delete(pref)
        db.commit()
    return MarketFeaturedOut(items=[])
