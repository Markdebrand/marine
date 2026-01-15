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
                elif profile == "erp":
                    from app.config.settings import (
                        ODOO_ERP_URL,
                        ODOO_ERP_DB,
                        ODOO_ERP_USER,
                        ODOO_ERP_PASSWORD
                    )
                    if not all([ODOO_ERP_URL, ODOO_ERP_DB, ODOO_ERP_USER, ODOO_ERP_PASSWORD]):
                        raise RuntimeError("Faltan variables Odoo ERP: defina ODOO_ERP_URL, ODOO_ERP_DB, ODOO_ERP_USER y ODOO_ERP_PASSWORD en .env")
                    print(f"DEBUG: Odoo ERP URL loaded: '{ODOO_ERP_URL}'") # DEBUG
                    _connectors[profile] = OdooConnector(
                        url=ODOO_ERP_URL,
                        db=ODOO_ERP_DB,
                        username=ODOO_ERP_USER,
                        password=ODOO_ERP_PASSWORD,
                    )
                else:
                    if not all([ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD]):
                        raise RuntimeError(f"Faltan variables Odoo DEFAULT para perfil '{profile}': defina ODOO_URL, ODOO_DB, ODOO_USER y ODOO_PASSWORD en .env")
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


# ============================================================================
# ACCOUNTING / INVOICES
# ============================================================================

INVOICE_DEFAULT_FIELDS: List[str] = [
    "id", "name", "partner_id", "invoice_date", "invoice_date_due",
    "amount_total", "amount_residual", "amount_untaxed", "amount_tax",
    "currency_id", "state", "payment_state", "access_token", "move_type",
]


def list_customer_invoices_by_email(
    *,
    email: str,
    limit: int = 100,
    offset: int = 0,
    order: Optional[str] = 'invoice_date desc, id desc',
    fields: Optional[List[str]] = None,
    profile: str = 'erp',
    include_paid: bool = True,
) -> List[dict]:
    """Lista facturas de cliente filtradas por email del partner.
    
    Realiza una búsqueda insensible a mayúsculas/minúsculas buscando primero
    los IDs del partner.
    """
    model_invoice = 'account.move'
    model_partner = 'res.partner'
    fields = fields or INVOICE_DEFAULT_FIELDS
    connector = _get_connector(profile)
    ctx = _build_ctx(connector)

    # 1. Buscar partners que coincidan con el email (ilike)
    # Buscamos ID y parent_id por si acaso, aunque solo usaremos el ID para filtrar facturas
    partner_domain: Domain = [('email', 'ilike', email)]
    partners = connector.search_read(model_partner, partner_domain, fields=['id'], context=ctx)
    
    if not partners:
        return []
        
    partner_ids = [p['id'] for p in partners]

    # 2. Buscar facturas asociadas a esos partners
    domain: Domain = [
        ('move_type', '=', 'out_invoice'),
        ('partner_id', 'in', partner_ids),
    ]
    
    if not include_paid:
        domain.append(('payment_state', 'in', ['not_paid', 'partial', 'in_payment']))
    
    rows = connector.search_read(
        model_invoice,
        domain,
        fields=fields,
        order=order,
        limit=limit,
        offset=offset,
        context=ctx,
    )
    
    return rows


def get_invoice_portal_url(
    invoice_id: int,
    access_token: Optional[str] = None,
    odoo_base_url: str = 'https://erp.hsotrade.com',
) -> str:
    """Genera URL del portal de Odoo para una factura."""
    base_url = odoo_base_url.rstrip('/')
    url = f'{base_url}/my/invoices/{invoice_id}'
    
    if access_token:
        url += f'?access_token={access_token}'
    
    return url
