"""merge heads: contact_requests and due_diligence branch

Revision ID: 20250915_merge_heads_contact_due
Revises: 20250904_alter_org_id_nullable_due_diligence_reports, 20250915_create_contact_requests_table
Create Date: 2025-09-15
"""
from __future__ import annotations

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = '20250915_merge_heads_contact_due'
down_revision = (
    '20250904_alter_org_id_nullable_due_diligence_reports',
    '20250915_create_contact_requests_table',
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op merge; unifies branches
    pass


def downgrade() -> None:
    # No-op merge
    pass
