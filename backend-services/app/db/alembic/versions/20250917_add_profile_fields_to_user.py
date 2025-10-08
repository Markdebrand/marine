"""Add profile fields to user table

Revision ID: 20250917_add_profile_fields_to_user
Revises: 20250915_merge_heads_contact_due
Create Date: 2025-09-17
"""
from __future__ import annotations

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = '20250917_add_profile_fields_to_user'
down_revision = '20250915_merge_heads_contact_due'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('company', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('website', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('bio', sa.String(length=1024), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('bio')
        batch_op.drop_column('website')
        batch_op.drop_column('company')
        batch_op.drop_column('phone')
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')
