"""merge branches to resolve multiple heads

Revision ID: 20251023_merge_heads
Revises: 0004_add_actual_geometry_columns, 20251023_stidx
Create Date: 2025-10-23 12:00:00.000000
"""

# revision identifiers, used by Alembic.
revision = '20251023_merge_heads'
down_revision = ('0004_add_actual_geometry_columns', '20251023_stidx')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration to join two divergent heads.
    pass


def downgrade() -> None:
    # Downgrade would be non-trivial because it would re-create divergence;
    # keep as a no-op to avoid accidental branch recreation.
    pass
