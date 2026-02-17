#!/usr/bin/env python3
"""
Script para verificar las relaciones entre vessels y countries.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import func
from app.db.database import SessionLocal
from app.db.models import MarineVessel, MarineCountry


def verify_vessel_country_relationships():
    """Verifica las relaciones entre vessels y countries."""
    db = SessionLocal()
    
    try:
        print("🔍 Verificando relaciones vessel-country...\n")
        
        # 1. Contar vessels con flag
        total_vessels = db.query(func.count(MarineVessel.id)).scalar()
        vessels_with_flag = db.query(func.count(MarineVessel.id)).filter(
            MarineVessel.flag.isnot(None)
        ).scalar()
        
        print(f"📊 Estadísticas generales:")
        print(f"   Total vessels: {total_vessels:,}")
        print(f"   Vessels con flag: {vessels_with_flag:,}")
        print(f"   Vessels sin flag: {(total_vessels - vessels_with_flag):,}")
        
        # 2. Verificar que los joins funcionan
        print(f"\n✅ Verificando JOIN con marine_country:")
        test_vessel = db.query(MarineVessel).filter(
            MarineVessel.flag.isnot(None)
        ).first()
        
        if test_vessel and test_vessel.country:
            print(f"   ✓ Vessel: {test_vessel.name}")
            print(f"   ✓ MMSI: {test_vessel.mmsi}")
            print(f"   ✓ Flag (MID): {test_vessel.flag}")
            print(f"   ✓ Country: {test_vessel.country.pais} / {test_vessel.country.country}")
        else:
            print(f"   ✗ No se pudo verificar el JOIN")
        
        # 3. Top 10 países con más vessels
        print(f"\n🌍 Top 10 países con más vessels:")
        country_stats = db.query(
            MarineCountry.pais,
            MarineCountry.country,
            func.count(MarineVessel.id).label('vessel_count')
        ).join(
            MarineVessel, MarineVessel.flag == MarineCountry.mid
        ).group_by(
            MarineCountry.mid, MarineCountry.pais, MarineCountry.country
        ).order_by(
            func.count(MarineVessel.id).desc()
        ).limit(10).all()
        
        for i, (pais, country, count) in enumerate(country_stats, 1):
            print(f"   {i:2d}. {pais:30s} - {count:,} vessels")
        
        # 4. Ejemplos de vessels con sus países
        print(f"\n📋 Ejemplos de vessels con información de país:")
        examples = db.query(MarineVessel).filter(
            MarineVessel.flag.isnot(None),
            MarineVessel.name.isnot(None)
        ).join(
            MarineCountry, MarineVessel.flag == MarineCountry.mid
        ).limit(15).all()
        
        for vessel in examples:
            print(f"   {vessel.name:30s} | MMSI: {vessel.mmsi:12s} | {vessel.country.country}")
        
        print(f"\n✅ Verificación completada exitosamente!")
        
    finally:
        db.close()


if __name__ == "__main__":
    verify_vessel_country_relationships()
