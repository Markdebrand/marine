from typing import Optional, List, TypedDict, Any, Iterable
import threading

from app.integrations.odoo.odoo_connector import OdooConnector
from app.integrations.odoo.odoo_crm_models import Client, Lead
from app.integrations.odoo.odoo_normalizers import (
    normalize_odoo_client,
    normalize_odoo_lead,
)
from app.config.settings import (
    ODOO_URL,
    ODOO_DB,
    ODOO_USER,
    ODOO_PASSWORD,
    ODOO_STAGING_URL,
    ODOO_STAGING_DB,
    ODOO_STAGING_USER,
    ODOO_STAGING_PASSWORD,
)

_connectors: dict[str, OdooConnector] = {}
_locks: dict[str, threading.Lock] = {}


def _get_lock(key: str) -> threading.Lock:
    lock = _locks.get(key)
    if lock is None:
        lock = threading.Lock()
        _locks[key] = lock
    return lock


def _get_connector(profile: str = "default") -> OdooConnector:
    """Devuelve un conector por perfil.

    Perfiles soportados:
    - "default": usa ODOO_URL/DB/USER/PASSWORD
    - "staging": usa ODOO_STAGING_* si están definidos
    """
    if profile not in _connectors:
        lock = _get_lock(f"odoo:{profile}")
        with lock:
            if profile not in _connectors:
                if profile == "staging":
                    if not all([ODOO_STAGING_URL, ODOO_STAGING_DB, ODOO_STAGING_USER, ODOO_STAGING_PASSWORD]):
                        raise RuntimeError("Faltan variables Odoo STAGING: defina ODOO_STAGING_URL, ODOO_STAGING_DB, ODOO_STAGING_USER y ODOO_STAGING_PASSWORD en .env")
                    _connectors[profile] = OdooConnector(
                        url=ODOO_STAGING_URL,
                        db=ODOO_STAGING_DB,
                        username=ODOO_STAGING_USER,
                        password=ODOO_STAGING_PASSWORD,
                    )
                else:
                    _connectors[profile] = OdooConnector(
                        url=ODOO_URL,
                        db=ODOO_DB,
                        username=ODOO_USER,
                        password=ODOO_PASSWORD,
                    )
    return _connectors[profile]


# Tipos utilitarios
Domain = List[list]


# Campos por defecto
LEAD_DEFAULT_FIELDS: List[str] = [
    "id", "name", "company_id", "partner_id", "email_from", "phone",
    "expected_revenue", "probability", "stage_id",
]
CLIENT_DEFAULT_FIELDS: List[str] = [
    "id", "name", "email", "phone", "company_id",
    "activity_ids", "country_id", "company_name", "street", "street2",
    "city", "state_id", "zip", "website", "category_id",
]


def _merge_domain(base: Optional[Iterable], extra: Optional[Iterable]) -> Domain:
    d: Domain = list(base or [])  # shallow copy
    if extra:
        d.extend(list(extra))
    return d


def _build_ctx(conn: OdooConnector, overrides: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    base: dict[str, Any] = {}
    if overrides:
        base.update(overrides)
    return conn.get_context_with_tz(base)


def list_clients(
    *,
    limit: int = 100,
    offset: int = 0,
    order: Optional[str] = None,
    fields: Optional[List[str]] = None,
    domain: Optional[List] = None,
    profile: str = "default",
) -> List[Client]:
    model = "res.partner"
    fields = fields or CLIENT_DEFAULT_FIELDS
    connector = _get_connector(profile)
    ctx = _build_ctx(connector)
    rows = connector.search_read(
        model,
        domain or [],
        fields=fields,
        order=order,
        limit=limit,
        offset=offset,
        context=ctx,
    )
    normalized = [normalize_odoo_client(r) for r in rows]
    return [Client(**r) for r in normalized]


def list_leads(
    *,
    limit: int = 100,
    offset: int = 0,
    order: Optional[str] = None,
    fields: Optional[List[str]] = None,
    domain: Optional[List] = None,
    profile: str = "default",
    context_overrides: Optional[dict] = None,
    company_id: int = 1,
) -> List[Lead]:
    model = "crm.lead"
    fields = fields or LEAD_DEFAULT_FIELDS
    connector = _get_connector(profile)
    ctx = _build_ctx(connector, context_overrides)
    dom = _merge_domain(domain, [["company_id", "=", int(company_id)]])

    rows = connector.search_read(
        model,
        dom,
        fields=fields,
        order=order,
        limit=limit,
        offset=offset,
        context=ctx,
    )
    normalized = [normalize_odoo_lead(r) for r in rows]
    return [Lead(**r) for r in normalized]


def diagnose(profile: str = "default") -> dict:
    """Diagnóstico rápido de conectividad y permisos.

    Devuelve: url, db, uid, tz, server_version y conteo de leads.
    """
    c = _get_connector(profile)
    uid = c.authenticate()
    tz = c.get_user_tz()
    try:
        ver = c.server_version()
    except Exception:
        ver = {}
    try:
        count = c.search_count("crm.lead", domain=[])
    except Exception as e:
        count = None
    return {
        "profile": profile,
        "url": c.url,
        "db": c.db,
        "uid": uid,
        "tz": tz,
        "server_version": ver,
        "lead_count": count,
    }


def list_pipeline_opportunities(
    *,
    limit: int = 2000,
    offset: int = 0,
    order: Optional[str] = "priority desc, id desc",
    fields: Optional[List[str]] = None,
    profile: str = "default",
    mine: bool = False,
    team_id: Optional[int] = None,
    include_archived: bool = False,
    company_id: int = 1,
) -> List[Lead]:
    """Lista los registros que aparecen en el Pipeline (kanban) de CRM.

    Dominio base: type = 'opportunity'. Por defecto sólo activos (active_test=true).
    """
    model = "crm.lead"
    fields = fields or LEAD_DEFAULT_FIELDS
    connector = _get_connector(profile)

    dom: Domain = [["type", "=", "opportunity"], ["company_id", "=", int(company_id)]]
    if mine:
        uid = connector.uid
        dom.append(["user_id", "=", uid])
    if team_id is not None:
        dom.append(["team_id", "=", int(team_id)])

    ctx_over: dict[str, Any] = {"active_test": False} if include_archived else {}
    ctx = _build_ctx(connector, ctx_over)

    rows = connector.search_read(
        model,
        dom,
        fields=fields,
        order=order,
        limit=limit,
        offset=offset,
        context=ctx,
    )
    normalized = [normalize_odoo_lead(r) for r in rows]
    return [Lead(**r) for r in normalized]
