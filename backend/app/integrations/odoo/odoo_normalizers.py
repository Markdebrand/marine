"""Normalizadores mínimos para entidades Odoo usadas por la API.

Actualmente sólo normalizamos `Lead` y `Client` corrigiendo valores False
de ciertos campos a `None` o listas vacías para encajar con los esquemas
Pydantic y evitar sorpresas en el consumidor.
"""

# No importamos helpers que no se usan aún para mantener el módulo liviano.


def normalize_odoo_lead(data: dict) -> dict:
    out = dict(data)
    for f in ("name", "email_from", "phone"):
        if out.get(f) is False:
            out[f] = None
    for f in ("company_id", "partner_id", "stage_id"):
        if out.get(f) is False:
            out[f] = []
    return out

def normalize_odoo_client(data: dict) -> dict:
    out = dict(data)
    for f in ("phone", "email", "name", "company_name", "street", "street2", "city", "website", "zip"):
        if out.get(f) is False:
            out[f] = None
    for f in ("company_id", "activity_ids", "country_id", "state_id", "category_id"):
        if out.get(f) is False:
            out[f] = []
    return out
