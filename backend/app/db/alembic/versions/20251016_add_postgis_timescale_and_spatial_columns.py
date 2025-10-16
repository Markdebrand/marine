"""add postgis/timescale extensions and spatial/jsonb columns

Revision ID: 20251016_add_postgis_timescale_and_spatial_columns
Revises: 
Create Date: 2025-10-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251016_spatial'
down_revision = '0002_create_base_tables'
branch_labels = None
depends_on = None


def upgrade():
    # NOTE: Extensions (PostGIS/TimescaleDB) and concurrent index creation are
    # intentionally not executed here. Create the extensions manually in the
    # server (e.g. via StackBuilder on Windows) and run index creation after
    # backfill using psql with CREATE INDEX CONCURRENTLY. Keeping this migration
    # limited to schema changes (adding temporary columns and FK) avoids
    # transactional errors on servers that lack the extension packages.

    # Add temporary geometry/jsonb columns to avoid table rewrite on large tables
    with op.batch_alter_table('vessel_state', schema=None) as batch_op:
        # geom_new will store intermediate geometry representation prior to converting
        # to proper PostGIS geometry type in a later step.
        batch_op.add_column(sa.Column('geom_new', postgresql.TEXT, nullable=True))

    with op.batch_alter_table('vessel_snapshot', schema=None) as batch_op:
        # last_geom_new is a temporary text column to be converted to geometry later.
        batch_op.add_column(sa.Column('last_geom_new', postgresql.TEXT, nullable=True))

    with op.batch_alter_table('marine_port', schema=None) as batch_op:
        batch_op.add_column(sa.Column('coords_new', postgresql.TEXT, nullable=True))
        batch_op.add_column(sa.Column('ext_refs_jsonb', postgresql.JSONB, nullable=True))

    with op.batch_alter_table('marine_vessel', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ext_refs_jsonb', postgresql.JSONB, nullable=True))

    # Indexes will be created manually after backfill using CREATE INDEX CONCURRENTLY.

    # Add FK constraint for latest_state_id (set null on delete)
    with op.batch_alter_table('vessel_snapshot', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_vessel_snapshot_latest_state', 'vessel_state', ['latest_state_id'], ['id'], ondelete='SET NULL')


def downgrade():
    # Remove columns added
    with op.batch_alter_table('vessel_state', schema=None) as batch_op:
        batch_op.drop_column('geom_new')

    with op.batch_alter_table('vessel_snapshot', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('fk_vessel_snapshot_latest_state', type_='foreignkey')
        except Exception:
            pass
        batch_op.drop_column('last_geom_new')
        batch_op.drop_column('latest_state_id')

    with op.batch_alter_table('marine_port', schema=None) as batch_op:
        batch_op.drop_column('coords_new')
        batch_op.drop_column('ext_refs_jsonb')

    with op.batch_alter_table('marine_vessel', schema=None) as batch_op:
        batch_op.drop_column('ext_refs_jsonb')

    # Note: extension removal intentionally omitted
