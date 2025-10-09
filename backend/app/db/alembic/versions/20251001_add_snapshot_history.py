"""allow multiple snapshots history per invitation/type

Revision ID: 20251001_add_snapshot_history
Revises: 20251001_add_sharing
Create Date: 2025-10-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20251001_add_snapshot_history'
down_revision = '20251001_add_sharing'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop unique constraint to allow multiple snapshots per (invitation_id, data_type)
    try:
        op.drop_constraint('uq_snapshot_invitation_type', 'sharing_snapshots', type_='unique')
    except Exception:
        pass
    # Optional new index to query latest quickly
    op.create_index('ix_sharing_snapshots_invitation_type_fetched', 'sharing_snapshots', ['invitation_id', 'data_type', 'fetched_at'])


def downgrade() -> None:
    op.drop_index('ix_sharing_snapshots_invitation_type_fetched', table_name='sharing_snapshots')
    # Recreate unique constraint (data loss risk if duplicates exist)
    try:
        op.create_unique_constraint('uq_snapshot_invitation_type', 'sharing_snapshots', ['invitation_id', 'data_type'])
    except Exception:
        pass
