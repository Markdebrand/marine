from sqlalchemy import inspect
import sys
from pathlib import Path

# Ensure project backend root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.database import engine  # type: ignore  # noqa: E402

insp = inspect(engine)
print("DB URL:", engine.url)
try:
    cols = insp.get_columns('user')
    print("user columns:")
    for c in cols:
        print(f" - {c['name']} ({str(c.get('type'))})")
except Exception as e:
    print("Error inspecting columns:", e)
