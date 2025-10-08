import os
import xmlrpc.client

# Carga variables del entorno .env si es posible
def load_env():
    from pathlib import Path
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    k, v = line.strip().split('=', 1)
                    os.environ.setdefault(k, v)

load_env()

url = os.environ.get('ODOO_URL', 'http://localhost:8069')
db = os.environ.get('ODOO_DB', '')
username = os.environ.get('ODOO_USER', '')
password = os.environ.get('ODOO_PASSWORD', '')

print(f"Conectando a Odoo: {url} DB: {db} USER: {username}")

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
print("UID:", uid)

if not uid:
    print("Error: No se pudo autenticar en Odoo (verifica usuario, password y DB)")
    exit(1)

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
print("Conexión a Odoo verificada. (Consulta específica de Argus eliminada)\n")
