"""Add last_profile_update_at to user

Revision ID: 20250917_add_last_profile_update_at_to_user
Revises: 20250917_add_profile_fields_to_user
Create Date: 2025-09-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250917_add_last_profile_update_at_to_user'
down_revision = '20250917_add_profile_fields_to_user'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('last_profile_update_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('last_profile_update_at')
