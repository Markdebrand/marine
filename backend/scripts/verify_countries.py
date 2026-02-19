#!/usr/bin/env python3
"""
Script para verificar los datos importados en la tabla marine_country.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz del backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import func
from app.db.database import SessionLocal
from app.db.models import MarineCountry


def verify_countries():
    """Verifica los datos de países en la base de datos."""
    db = SessionLocal()
    
    try:
        # Contar total de países
        total = db.query(func.count(MarineCountry.mid)).scalar()
        print(f"✅ Total de países en la base de datos: {total}")
        
        # Mostrar algunos ejemplos
        print("\n📋 Primeros 10 registros:")
        countries = db.query(MarineCountry).order_by(MarineCountry.mid).limit(10).all()
        for country in countries:
            print(f"   MID {country.mid}: {country.pais} / {country.country}")
        
        # Mostrar algunos ejemplos del medio
        print("\n📋 Algunos registros del rango 400-500:")
        countries = db.query(MarineCountry).filter(
            MarineCountry.mid >= 400,
            MarineCountry.mid < 500
        ).order_by(MarineCountry.mid).limit(5).all()
        for country in countries:
            print(f"   MID {country.mid}: {country.pais} / {country.country}")
        
        # Verificar un país específico
        print("\n🔍 Buscando MID 710 (Brasil):")
        brasil = db.query(MarineCountry).filter(MarineCountry.mid == 710).first()
        if brasil:
            print(f"   ✅ Encontrado: {brasil.pais} / {brasil.country}")
        else:
            print("   ❌ No encontrado")
        
    finally:
        db.close()


if __name__ == "__main__":
    verify_countries()
