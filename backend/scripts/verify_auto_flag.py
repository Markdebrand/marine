#!/usr/bin/env python3
"""
Script para verificar que los nuevos barcos tengan el flag asignado automáticamente.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.database import SessionLocal
from app.db.models import MarineVessel, MarineCountry


def verify_auto_flag():
    """Verifica la asignación automática de flag."""
    db = SessionLocal()
    
    # MMSI de prueba para un país existente (ej: 710 - Brasil)
    test_mmsi = "710123456"
    test_name = "TEST_AUTO_FLAG_VESSEL"
    
    try:
        print(f"🚀 Creando barco de prueba con MMSI: {test_mmsi}...")
        
        # Eliminar si ya existe
        db.query(MarineVessel).filter(MarineVessel.mmsi == test_mmsi).delete()
        db.commit()
        
        # Crear nuevo barco vía ORM
        new_vessel = MarineVessel(
            mmsi=test_mmsi,
            name=test_name
        )
        db.add(new_vessel)
        db.commit()
        db.refresh(new_vessel)
        
        print(f"✅ Barco creado ID: {new_vessel.id}")
        print(f"✅ MMSI: {new_vessel.mmsi}")
        print(f"✅ Flag asignado: {new_vessel.flag}")
        
        if new_vessel.flag == 710:
            print("🎉 ÉXITO: El flag se asignó automáticamente al crear el barco vía ORM.")
        else:
            print("❌ ERROR: El flag no coincide con el prefijo esperado (710).")
            
        # Verificar relación con el país
        if new_vessel.country:
            print(f"✅ País relacionado: {new_vessel.country.pais} / {new_vessel.country.country}")
        else:
            print("⚠️ Nota: El país no se pudo relacionar (¿existe el MID 710 en la tabla?)")
            
        # Limpiar
        db.delete(new_vessel)
        db.commit()
        print("\n🗑️ Barco de prueba eliminado.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la verificación: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    verify_auto_flag()
