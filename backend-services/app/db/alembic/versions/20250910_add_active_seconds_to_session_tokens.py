"""add active_seconds to session_tokens

Revision ID: 20250910_add_active_seconds
Revises: 231aac56d8b8_merge_heads
Create Date: 2025-09-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.

revision: str = '20250910_add_active_seconds'
down_revision = ('20250904_add_usage_counters', '20250904_fix_subscriptions_columns')
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('session_tokens', sa.Column('active_seconds', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('session_tokens', 'active_seconds')
