#!/usr/bin/env python3
"""
Script de backfill por batches para convertir columnas placeholder a geometry/JSONB.
Uso: configurar conexión via DATABASE_URL env var o usar .env loader.

Este script convierte:
- vessel_state.geom_new <- ST_SetSRID(ST_MakePoint(lon, lat), 4326) si la columna geom contiene 'lat,lon' o WKT.
- vessel_snapshot.last_geom_new <- similar
- marine_port.coords_new <- similar
- ext_refs_jsonb <- ext_refs::jsonb

El script opera en batches por id y hace sleep entre batches para limitar IO.
"""
from __future__ import annotations

import os
import time
import logging
from sqlalchemy import text
from sqlalchemy import create_engine
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.getenv('ALEMBIC_DATABASE_URL') or os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or os.getenv('POSTGRES_DSN')
if not DATABASE_URL:
    # Build from POSTGRES_* env variables
    user = os.getenv('POSTGRES_USER', 'postgres')
    pwd = os.getenv('POSTGRES_PASSWORD', '')
    host = os.getenv('POSTGRES_HOST', '127.0.0.1')
    port = os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('POSTGRES_DB', 'hsomarine')
    if pwd:
        DATABASE_URL = f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"
    else:
        DATABASE_URL = f"postgresql+psycopg://{user}@{host}:{port}/{db}"

engine = create_engine(DATABASE_URL)

BATCH_SIZE = int(os.getenv('BACKFILL_BATCH_SIZE', '5000'))
SLEEP_SECONDS = float(os.getenv('BACKFILL_SLEEP_SECONDS', '0.5'))


def run_backfill_geom(table: str, src_col: str, dst_col: str, id_col: str = 'id'):
    """Backfill geometry column in batches. Supports source in format 'lat,lon' or WKT POINT(...)"""
    log.info('Starting backfill %s.%s <- %s', table, dst_col, src_col)
    with engine.begin() as conn:
        # get min/max id
        r = conn.execute(text(f"SELECT min({id_col}), max({id_col}) FROM {table}"))
        min_id, max_id = r.fetchone()
        if min_id is None:
            log.info('Table %s empty, skipping', table)
            return
    cur = min_id
    while cur <= max_id:
        upper = cur + BATCH_SIZE - 1
        log.info('Processing %s ids %s..%s', table, cur, upper)
        # Update clause: try parse 'lat,lon' else try ST_GeomFromText
        # Uses a safe expression - if parsing fails, result will be NULL
        update_sql = f'''
        UPDATE {table}
        SET {dst_col} = COALESCE(
            CASE
                WHEN {src_col} ~ '^\\s*-?\\d+(\\.\\d+)?\\s*,\\s*-?\\d+(\\.\\d+)?\\s*$' THEN
                    ST_SetSRID(ST_MakePoint(split_part({src_col}, ',', 2)::double precision, split_part({src_col}, ',', 1)::double precision), 4326)
                ELSE
                    ST_SetSRID(ST_GeomFromText({src_col}), 4326)
            END
        , {dst_col})
        WHERE {id_col} BETWEEN :low AND :high
        '''
        with engine.begin() as conn:
            conn.execute(text(update_sql), {'low': cur, 'high': upper})
        cur = upper + 1
        time.sleep(SLEEP_SECONDS)
    log.info('Finished backfill geom for %s', table)


def run_backfill_jsonb(table: str, src_col: str, dst_col: str, id_col: str = 'id'):
    log.info('Starting JSONB backfill %s.%s <- %s', table, dst_col, src_col)
    with engine.begin() as conn:
        r = conn.execute(text(f"SELECT min({id_col}), max({id_col}) FROM {table}"))
        min_id, max_id = r.fetchone()
        if min_id is None:
            log.info('Table %s empty, skipping', table)
            return
    cur = min_id
    while cur <= max_id:
        upper = cur + BATCH_SIZE - 1
        log.info('Processing %s ids %s..%s', table, cur, upper)
        update_sql = f"UPDATE {table} SET {dst_col} = ({src_col})::jsonb WHERE {id_col} BETWEEN :low AND :high"
        with engine.begin() as conn:
            conn.execute(text(update_sql), {'low': cur, 'high': upper})
        cur = upper + 1
        time.sleep(SLEEP_SECONDS)
    log.info('Finished JSONB backfill for %s', table)


def main():
    # Geometries
    run_backfill_geom('vessel_state', 'geom', 'geom_new')
    run_backfill_geom('vessel_snapshot', 'last_geom', 'last_geom_new', id_col='mmsi')
    run_backfill_geom('marine_port', 'coords', 'coords_new')

    # JSONB
    run_backfill_jsonb('marine_vessel', 'ext_refs', 'ext_refs_jsonb')
    run_backfill_jsonb('marine_port', 'ext_refs', 'ext_refs_jsonb')

    log.info('Backfill complete. Create indexes CONCURRENTLY on new columns and swap names when ready.')


if __name__ == '__main__':
    main()
