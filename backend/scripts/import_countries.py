#!/usr/bin/env python3
"""
Script para importar datos de países a la tabla marine_country.

Uso:
    python import_countries.py sample_countries.csv
"""
import sys
import csv
from pathlib import Path

# Agregar el directorio raíz del backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import MarineCountry


def import_countries_from_csv(csv_file_path: str):
    """
    Importa países desde un archivo CSV a la tabla marine_country.
    
    Args:
        csv_file_path: Ruta al archivo CSV con columnas: mid,pais,country
    """
    db: Session = SessionLocal()
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            countries_added = 0
            countries_updated = 0
            
            for row in reader:
                mid = int(row['mid'])
                pais = row['pais']
                country = row['country']
                
                # Verificar si el país ya existe
                existing_country = db.query(MarineCountry).filter(
                    MarineCountry.mid == mid
                ).first()
                
                if existing_country:
                    # Actualizar si ya existe
                    existing_country.pais = pais
                    existing_country.country = country
                    countries_updated += 1
                    print(f"Actualizado: {mid} - {pais} / {country}")
                else:
                    # Crear nuevo registro
                    new_country = MarineCountry(
                        mid=mid,
                        pais=pais,
                        country=country
                    )
                    db.add(new_country)
                    countries_added += 1
                    print(f"Agregado: {mid} - {pais} / {country}")
            
            # Confirmar los cambios
            db.commit()
            
            print(f"\n✅ Importación completada:")
            print(f"   - Países agregados: {countries_added}")
            print(f"   - Países actualizados: {countries_updated}")
            print(f"   - Total procesados: {countries_added + countries_updated}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la importación: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python import_countries.py <archivo_csv>")
        print("Ejemplo: python import_countries.py sample_countries.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"❌ Error: El archivo {csv_file} no existe")
        sys.exit(1)
    
    import_countries_from_csv(csv_file)
