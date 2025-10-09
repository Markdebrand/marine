from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


from app.db.database import get_db
from app.db.models import Release, ReleaseSection
from app.auth.dependencies import require_roles

# Si más adelante quieres restringir a admins:
# from app.auth.dependencies import get_current_user
# and verify role/permission inside create endpoint.

router = APIRouter(prefix="/releases", tags=["releases"])


class ReleaseSectionIn(BaseModel):
    title: str = Field(..., max_length=50)
    content: str = Field(..., max_length=250)


class ReleaseCreate(BaseModel):
    title: str = Field(..., max_length=50)
    version: str = Field(..., max_length=32)
    type: str = Field(..., max_length=32)
    short_description: Optional[str] = Field(None, max_length=500)
    sections: List[ReleaseSectionIn] = Field(default_factory=list)


class ReleaseSectionOut(BaseModel):
    id: int
    title: str
    content: str
    position: int

    class Config:
        from_attributes = True


class ReleaseOut(BaseModel):
    id: int
    title: str
    version: str
    type: str
    short_description: Optional[str]
    created_at: datetime
    sections: List[ReleaseSectionOut]

    class Config:
        from_attributes = True


@router.get("", response_model=List[ReleaseOut])
def list_releases(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Filtro por coincidencia en title o version"),
    type: Optional[str] = Query(None, description="Filtrar por type"),
):
    query = db.query(Release)
    if q:
        like = f"%{q}%"
        query = query.filter((Release.title.ilike(like)) | (Release.version.ilike(like)))
    if type:
        query = query.filter(Release.type == type)
    items = (
        query.order_by(Release.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return items


@router.get("/{release_id}", response_model=ReleaseOut)
def get_release(release_id: int, db: Session = Depends(get_db)):
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release no encontrado")
    return release


@router.post(
    "",
    response_model=ReleaseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin"))],
)
def create_release(data: ReleaseCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Release)
        .filter(Release.version == data.version, Release.type == data.type)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Release con misma version y type ya existe")
    release = Release(
        title=data.title,
        version=data.version,
        type=data.type,
        short_description=data.short_description,
    )
    db.add(release)
    db.flush()
    for idx, sec in enumerate(data.sections):
        db.add(
            ReleaseSection(
                release_id=release.id,
                title=sec.title,
                content=sec.content,
                position=idx,
            )
        )
    db.commit()
    db.refresh(release)
    return release


@router.put(
    "/{release_id}",
    response_model=ReleaseOut,
    dependencies=[Depends(require_roles("admin"))],
)
def update_release(release_id: int, data: ReleaseCreate, db: Session = Depends(get_db)):
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release no encontrado")
    exists = db.query(Release).filter(
        Release.version == data.version,
        Release.type == data.type,
        Release.id != release_id,
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Ya existe otro release con esa version y type")
    setattr(release, "title", data.title)
    setattr(release, "version", data.version)
    setattr(release, "type", data.type)
    setattr(release, "short_description", data.short_description)
    release.sections.clear()
    db.flush()
    for idx, sec in enumerate(data.sections):
        db.add(
            ReleaseSection(
                release_id=release.id,
                title=sec.title,
                content=sec.content,
                position=idx,
            )
        )
    db.commit()
    db.refresh(release)
    return release


@router.delete(
    "/{release_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
def delete_release(release_id: int, db: Session = Depends(get_db)):
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release no encontrado")
    db.delete(release)
    db.commit()
    return None
