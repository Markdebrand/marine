"""Create activation_tokens table

Revision ID: 20250917_add_activation_tokens_table
Revises: 20250917_drop_form_pending_table
Create Date: 2025-09-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250917_add_activation_tokens_table'
# Merge heads: drop_form_pending_table y drop_contact_requests_table
down_revision = ('20250917_drop_form_pending_table', '20250917_drop_contact_requests_table')
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'activation_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    )
    # Indexes & unique constraints
    op.create_index('ix_activation_tokens_user_id', 'activation_tokens', ['user_id'], unique=False)
    op.create_index('ix_activation_tokens_token_hash', 'activation_tokens', ['token_hash'], unique=True)


def downgrade() -> None:
    try:
        op.drop_index('ix_activation_tokens_token_hash', table_name='activation_tokens')
    except Exception:
        pass
    try:
        op.drop_index('ix_activation_tokens_user_id', table_name='activation_tokens')
    except Exception:
        pass
    op.drop_table('activation_tokens')
