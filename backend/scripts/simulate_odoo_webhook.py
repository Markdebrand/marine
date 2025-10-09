import os, sys, json, hmac, hashlib, requests

BASE = os.environ.get('API_BASE', 'http://127.0.0.1:8000')
SECRET = os.environ.get('ODOO_WEBHOOK_SECRET', '')
URL = f"{BASE.rstrip('/')}/odoo/customer-confirmed"

body = {
    "email": os.environ.get('TEST_EMAIL', 'user@example.com'),
    "first_name": "Test",
    "last_name": "User",
    "company": "HSO",
    "plan": os.environ.get('TEST_PLAN', 'started'),
    "lead_id": os.environ.get('TEST_LEAD_ID', 'L-1001'),
    "partner_id": os.environ.get('TEST_PARTNER_ID', 'P-2002'),
}
raw = json.dumps(body, separators=(',', ':')).encode('utf-8')
if not SECRET:
    print('Set ODOO_WEBHOOK_SECRET in env', file=sys.stderr)
    sys.exit(2)
sig = hmac.new(SECRET.encode('utf-8'), raw, hashlib.sha256).hexdigest()
headers = {"Content-Type": "application/json", "X-Odoo-Signature": sig}

r = requests.post(URL, data=raw, headers=headers, timeout=10)
print(r.status_code)
print(r.text)
