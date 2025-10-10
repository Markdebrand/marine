"""add plaid identity verifications table

Revision ID: 20250930_add_plaid_identity_verifications
Revises: 231aac56d8b8_merge_heads
Create Date: 2025-09-30
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250930_add_plaid_identity_verifications'
down_revision = '231aac56d8b8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'plaid_identity_verifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plaid_session_id', sa.String(length=128), nullable=False),
        sa.Column('template_id', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('last_payload', sa.String(length=4000), nullable=True),
        sa.Column('attempt_no', sa.Integer(), server_default='1', nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_reason', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_plaid_identity_verifications_user_id', 'plaid_identity_verifications', ['user_id'])
    op.create_index('ix_plaid_identity_verifications_plaid_session_id', 'plaid_identity_verifications', ['plaid_session_id'], unique=True)
    op.create_index('ix_plaid_identity_verifications_status', 'plaid_identity_verifications', ['status'])
    op.create_index('ix_plaid_idv_user_status', 'plaid_identity_verifications', ['user_id', 'status'])


def downgrade():
    op.drop_index('ix_plaid_idv_user_status', table_name='plaid_identity_verifications')
    op.drop_index('ix_plaid_identity_verifications_status', table_name='plaid_identity_verifications')
    op.drop_index('ix_plaid_identity_verifications_plaid_session_id', table_name='plaid_identity_verifications')
    op.drop_index('ix_plaid_identity_verifications_user_id', table_name='plaid_identity_verifications')
    op.drop_table('plaid_identity_verifications')
