#!/usr/bin/env python
"""Lista leads de Odoo Staging usando la capa de servicio.

Uso:
  python scripts/fetch_odoo_staging_leads.py [--limit 20] [--offset 0]
Requiere variables ODOO_STAGING_* en .env.
"""
import argparse
from pprint import pprint

from app.integrations.odoo.odoo_service import list_leads


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--order", type=str, default="create_date desc")
    args = ap.parse_args()

    leads = list_leads(limit=args.limit, offset=args.offset, order=args.order, profile="staging")
    for i, l in enumerate(leads, 1):
        print(f"{i:02d}. id={l.id} name={l.name!r} email={l.email_from!r} stage={l.stage_id}")
    if not leads:
        print("No hay leads (verifica ODOO_STAGING_* en .env)")


if __name__ == "__main__":
    main()
