"""create plaid_items table

Revision ID: 20250910_create_plaid_items
Revises: 20250910_add_active_seconds_to_session_tokens
Create Date: 2025-09-10
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250910_create_plaid_items'
down_revision = '20250910_add_active_seconds'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'plaid_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_id', sa.String(length=128), nullable=False),
        sa.Column('access_token_enc', sa.LargeBinary(), nullable=False),
        sa.Column('institution_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.UniqueConstraint('user_id', 'item_id', name='uq_plaid_items_user_item'),
    )
    op.create_index('ix_plaid_items_user_created', 'plaid_items', ['user_id', 'id'])


def downgrade() -> None:
    op.drop_index('ix_plaid_items_user_created', table_name='plaid_items')
    op.drop_table('plaid_items')
