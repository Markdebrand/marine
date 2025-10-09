from fastapi import APIRouter, HTTPException, Query, Response
import json
from typing import Optional, List

from app.integrations.odoo.odoo_crm_models import Client, Lead
from app.integrations.odoo.odoo_service import (
    list_clients,
    list_leads,
    diagnose,
    list_pipeline_opportunities,
)

router = APIRouter(prefix="/odoo", tags=["Odoo"])


def _parse_domain(domain: Optional[str]) -> List:
    if not domain:
        return []
    try:
        parsed = json.loads(domain)
        if isinstance(parsed, list):
            return parsed
        raise ValueError("domain debe ser JSON tipo lista")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"domain inválido: {e}")


@router.get("/clients", response_model=List[Client])
def clients(
    response: Response,
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    order: Optional[str] = None,
    profile: str = Query("default", pattern="^(default|staging)$"),
):
    try:
        data = list_clients(limit=limit, offset=offset, order=order, profile=profile)
        response.headers["Cache-Control"] = "public, max-age=60"
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/leads", response_model=List[Lead])
def leads(
    response: Response,
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    order: Optional[str] = None,
    profile: str = Query("default", pattern="^(default|staging)$"),
    include_archived: bool = Query(False, description="Si true, incluye registros archivados (active_test=false)"),
    domain: Optional[str] = Query(None, description="Dominio Odoo en JSON (por ejemplo: [[\"active\",\"=\",False]])"),
    company_id: int = Query(1, ge=1, description="Filtrar por compañía (company_id)"),
):
    try:
        domain_list = _parse_domain(domain)

        ctx_overrides = {}
        if include_archived:
            ctx_overrides["active_test"] = False

        data = list_leads(
            limit=limit,
            offset=offset,
            order=order,
            domain=domain_list or None,
            profile=profile,
            context_overrides=ctx_overrides or None,
            company_id=company_id,
        )
        response.headers["Cache-Control"] = "public, max-age=60"
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/diagnostics")
def diagnostics(profile: str = Query("default", pattern="^(default|staging)$")):
    try:
        return diagnose(profile)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/pipeline", response_model=List[Lead])
def pipeline(
    response: Response,
    profile: str = Query("default", pattern="^(default|staging)$"),
    mine: bool = Query(False, description="Sólo mis oportunidades (user_id=uid)"),
    team_id: Optional[int] = Query(None, description="Filtrar por equipo de ventas (team_id)"),
    include_archived: bool = Query(False, description="Incluir archivados (active_test=false)"),
    limit: int = Query(2000, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    order: Optional[str] = Query("priority desc, id desc"),
    company_id: int = Query(1, ge=1, description="Filtrar por compañía (company_id)"),
):
    try:
        data = list_pipeline_opportunities(
            profile=profile,
            mine=mine,
            team_id=team_id,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
            order=order,
            company_id=company_id,
        )
        response.headers["Cache-Control"] = "public, max-age=60"
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))