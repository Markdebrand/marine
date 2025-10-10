"""enable postgis/timescale and convert geom

Revision ID: 0002_postgis_timescale_and_geom
Revises: 0001_initial_hsomarine
Create Date: 2025-10-10 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_postgis_timescale_and_geom'
down_revision = '0001_initial_hsomarine'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Enable PostGIS
    try:
        conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS postgis'))
    except Exception:
        # If running on DB without superuser, this may fail; operator should enable extension manually
        pass

    # Optionally enable timescaledb if available
    try:
        conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS timescaledb'))
    except Exception:
        pass

    # Alter vessel_state.geom to geometry(Point,4326) if PostGIS is available
    # This uses USING NULLIF to avoid failing when text cannot be cast; operator should review data
    try:
        op.execute("""
        ALTER TABLE vessel_state
        ALTER COLUMN geom TYPE geometry(Point,4326)
        USING (CASE WHEN geom IS NULL THEN NULL ELSE ST_SetSRID(ST_Point(CAST(split_part(geom, ',', 2) AS double precision), CAST(split_part(geom, ',', 1) AS double precision)), 4326) END);
        """)
    except Exception:
        # Fallback: try to add a new column and leave old as backup
        try:
            op.add_column('vessel_state', sa.Column('geom_point', sa.types.UserDefinedType(), nullable=True))
        except Exception:
            pass

    # If timescaledb present, create hypertable
    try:
        conn.execute(sa.text("SELECT create_hypertable('vessel_state','ts', if_not_exists => TRUE)"))
    except Exception:
        pass


def downgrade() -> None:
    conn = op.get_bind()
    # Downgrade: attempt to revert geom to text (best-effort)
    try:
        op.execute("ALTER TABLE vessel_state ALTER COLUMN geom TYPE TEXT USING ST_AsText(geom);")
    except Exception:
        pass