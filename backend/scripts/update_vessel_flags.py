#!/usr/bin/env python3
"""
Script para actualizar el campo flag de marine_vessel con el MID (primeros 3 dígitos del MMSI).

Este script:
1. Extrae los primeros 3 dígitos del MMSI de cada vessel
2. Valida que el MID existe en la tabla marine_country
3. Actualiza el campo flag con el valor del MID
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import func
from app.db.database import SessionLocal
from app.db.models import MarineVessel, MarineCountry


def update_vessel_flags():
    """Actualiza los flags de todos los vessels basándose en el MMSI."""
    db = SessionLocal()
    
    try:
        # Obtener todos los MIDs válidos de marine_country
        valid_mids = set(mid for (mid,) in db.query(MarineCountry.mid).all())
        print(f"📋 MIDs válidos en marine_country: {len(valid_mids)}")
        
        # Obtener todos los vessels
        vessels = db.query(MarineVessel).all()
        total_vessels = len(vessels)
        print(f"🚢 Total de vessels a procesar: {total_vessels}\n")
        
        # Contadores
        updated = 0
        invalid_mmsi = 0
        mid_not_found = 0
        already_set = 0
        
        # Procesar cada vessel
        for i, vessel in enumerate(vessels, 1):
            if i % 1000 == 0:
                print(f"Procesando: {i}/{total_vessels}...")
            
            # Skip si ya tiene flag
            if vessel.flag is not None:
                already_set += 1
                continue
            
            # Validar MMSI
            if not vessel.mmsi or len(vessel.mmsi) < 3:
                invalid_mmsi += 1
                continue
            
            # Extraer MID (primeros 3 dígitos)
            try:
                mid = int(vessel.mmsi[:3])
            except ValueError:
                invalid_mmsi += 1
                continue
            
            # Verificar si el MID existe en marine_country
            if mid not in valid_mids:
                mid_not_found += 1
                if mid_not_found <= 10:  # Mostrar solo los primeros 10 ejemplos
                    print(f"⚠️  MID {mid} no encontrado (MMSI: {vessel.mmsi}, Vessel: {vessel.name})")
                continue
            
            # Actualizar el flag
            vessel.flag = mid
            updated += 1
        
        # Commit de todos los cambios
        db.commit()
        
        # Resumen
        print(f"\n{'='*60}")
        print(f"✅ Actualización completada:")
        print(f"{'='*60}")
        print(f"  📊 Total vessels procesados:     {total_vessels:,}")
        print(f"  ✅ Flags actualizados:            {updated:,}")
        print(f"  ⏭️  Ya tenían flag:                {already_set:,}")
        print(f"  ❌ MMSI inválido o muy corto:     {invalid_mmsi:,}")
        print(f"  ⚠️  MID no encontrado en tabla:   {mid_not_found:,}")
        print(f"{'='*60}")
        
        if mid_not_found > 10:
            print(f"\n💡 Nota: Se encontraron {mid_not_found} vessels con MID no registrado.")
            print(f"   Los primeros 10 se mostraron arriba. Considera agregar estos")
            print(f"   países a la tabla marine_country si son válidos.")
        
        # Mostrar algunos ejemplos de vessels actualizados
        print(f"\n📋 Ejemplos de vessels actualizados:")
        examples = db.query(MarineVessel).filter(
            MarineVessel.flag.isnot(None)
        ).join(
            MarineCountry, MarineVessel.flag == MarineCountry.mid
        ).limit(10).all()
        
        for vessel in examples:
            print(f"   MMSI: {vessel.mmsi} -> MID: {vessel.flag} -> {vessel.country.pais} / {vessel.country.country}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la actualización: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🔄 Iniciando actualización de flags de vessels...\n")
    update_vessel_flags()
