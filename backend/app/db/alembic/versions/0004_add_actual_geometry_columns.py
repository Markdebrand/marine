"""add actual PostGIS geometry columns

Revision ID: 0004_add_actual_geometry_columns
Revises: 0003_create_remaining_tables
Create Date: 2025-10-16 01:30:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0004_add_actual_geometry_columns'
down_revision = '0003_create_remaining_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add proper geometry columns (requires PostGIS installed on DB)
    op.execute("ALTER TABLE vessel_state ADD COLUMN IF NOT EXISTS geom_geom geometry(POINT,4326);")
    op.execute("ALTER TABLE vessel_snapshot ADD COLUMN IF NOT EXISTS last_geom_geom geometry(POINT,4326);")
    op.execute("ALTER TABLE marine_port ADD COLUMN IF NOT EXISTS coords_geom geometry(POINT,4326);")


def downgrade():
    op.execute("ALTER TABLE marine_port DROP COLUMN IF EXISTS coords_geom;")
    op.execute("ALTER TABLE vessel_snapshot DROP COLUMN IF EXISTS last_geom_geom;")
    op.execute("ALTER TABLE vessel_state DROP COLUMN IF EXISTS geom_geom;")
