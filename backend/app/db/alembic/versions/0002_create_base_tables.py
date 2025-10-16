"""create base tables for HSOMarine

Revision ID: 0002_create_base_tables
Revises: 0001_baseline_hsomarine
Create Date: 2025-10-16 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_create_base_tables'
down_revision = '0001_baseline_hsomarine'
branch_labels = None
depends_on = None


def upgrade():
    # Create vessel_state table
    op.create_table(
        'vessel_state',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('mmsi', sa.String(16), nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('geom', postgresql.TEXT, nullable=True),
        sa.Column('sog', sa.Float, nullable=True),
        sa.Column('cog', sa.Float, nullable=True),
        sa.Column('heading', sa.Float, nullable=True),
        sa.Column('nav_status', sa.String(50), nullable=True),
        sa.Column('src', sa.String(64), nullable=True),
    )

    # Create vessel_snapshot table
    op.create_table(
        'vessel_snapshot',
        sa.Column('mmsi', sa.String(16), primary_key=True),
        sa.Column('last_ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_geom', postgresql.TEXT, nullable=True),
        sa.Column('sog', sa.Float, nullable=True),
        sa.Column('cog', sa.Float, nullable=True),
        sa.Column('heading', sa.Float, nullable=True),
        sa.Column('nav_status', sa.String(50), nullable=True),
        sa.Column('latest_state_id', sa.Integer, nullable=True),
    )
    # Create marine_port table
    op.create_table(
        'marine_port',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('unlocode', sa.String(16), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('country', sa.String(128), nullable=True),
        sa.Column('ext_refs', postgresql.JSONB, nullable=True),
        sa.Column('coords', postgresql.TEXT, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create marine_vessel table
    op.create_table(
        'marine_vessel',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('mmsi', sa.String(16), nullable=False),
        sa.Column('imo', sa.String(16), nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('type', sa.String(64), nullable=True),
        sa.Column('flag', sa.String(64), nullable=True),
        sa.Column('ext_refs', postgresql.JSONB, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table('marine_vessel')
    op.drop_table('marine_port')
    op.drop_table('vessel_snapshot')
    op.drop_table('vessel_state')
