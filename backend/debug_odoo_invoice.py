
import sys
from app.integrations.odoo.odoo_service import _get_connector

# Load configured URL
from app.config.settings import ODOO_ERP_URL, ODOO_ERP_DB, ODOO_ERP_USER, ODOO_ERP_PASSWORD
print(f"Connecting to {ODOO_ERP_URL} as {ODOO_ERP_USER}")

conn = _get_connector("erp")

email = "gabrielmontes@markdebrand.com"

# 1. Search Partner
print(f"Searching partner by email: {email}")
partners = conn.search_read("res.partner", [("email", "ilike", email)], fields=["id", "name", "email", "parent_id"])
print(f"Found partners: {partners}")

if not partners:
    print("No partner found with 'ilike'. trying exact match")
    partners = conn.search_read("res.partner", [("email", "=", email)], fields=["id", "name", "email"])
    print(f"Found partners exact: {partners}")

if not partners:
    print("FATAL: Partner not found.")
    sys.exit(1)

partner_ids = [p["id"] for p in partners]

# 2. Search Invoices using partner_id IN [...]
print(f"Searching invoices for partner_ids: {partner_ids}")
domain = [
    ("move_type", "=", "out_invoice"),
    ("partner_id", "in", partner_ids)
]
invoices = conn.search_read("account.move", domain, fields=["id", "name", "payment_state", "amount_total"], limit=5)
print(f"Found invoices (by partner_id IN): {invoices}")

# 3. Check what the service does: partner_id.email = ...
print(f"Searching invoices via partner_id.email = {email}")
domain_service = [
    ("move_type", "=", "out_invoice"),
    ("partner_id.email", "=", email)
]
invoices_service = conn.search_read("account.move", domain_service, fields=["id", "name"], limit=5)
print(f"Found invoices (via service query): {invoices_service}")
