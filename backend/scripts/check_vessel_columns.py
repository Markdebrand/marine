#!/usr/bin/env python3
"""
Script rápido para verificar las columnas de marine_vessel.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import inspect
from app.db.database import engine


def check_columns():
    """Verifica las columnas de la tabla marine_vessel."""
    inspector = inspect(engine)
    columns = inspector.get_columns('marine_vessel')
    
    print("📋 Columnas en marine_vessel:")
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        print(f"   - {col['name']:20s} {str(col['type']):20s} {nullable}")


if __name__ == "__main__":
    check_columns()
