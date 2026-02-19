#!/usr/bin/env python3
"""
Script para analizar los datos de marine_vessel y ver ejemplos de MMSI.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import func
from app.db.database import SessionLocal
from app.db.models import MarineVessel


def analyze_vessels():
    """Analiza los datos de vessels."""
    db = SessionLocal()
    
    try:
        # Contar total de vessels
        total = db.query(func.count(MarineVessel.id)).scalar()
        print(f"Total de vessels: {total}")
        
        # Contar cuántos tienen flag
        with_flag = db.query(func.count(MarineVessel.id)).filter(
            MarineVessel.flag.isnot(None)
        ).scalar()
        print(f"Vessels con flag: {with_flag}")
        print(f"Vessels sin flag: {total - with_flag}")
        
        # Mostrar algunos ejemplos de MMSI
        print("\nEjemplos de MMSI:")
        vessels = db.query(MarineVessel).limit(10).all()
        for vessel in vessels:
            mid = vessel.mmsi[:3] if vessel.mmsi and len(vessel.mmsi) >= 3 else "N/A"
            print(f"  MMSI: {vessel.mmsi} -> MID: {mid}, Name: {vessel.name}, Flag: {vessel.flag}")
        
    finally:
        db.close()


if __name__ == "__main__":
    analyze_vessels()
