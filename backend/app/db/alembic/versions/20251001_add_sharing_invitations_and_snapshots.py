"""add sharing invitations and snapshots

Revision ID: 20251001_add_sharing
Revises: 20250930_add_plaid_identity_verifications
Create Date: 2025-10-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '20251001_add_sharing'
down_revision = '20250930_add_plaid_identity_verifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sharing_invitations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('inviter_user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invitee_user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('invitee_email', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=72), nullable=False, unique=True),
        sa.Column('requested_scopes', sa.Text(), nullable=False),
        sa.Column('granted_scopes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('plaid_item_id', sa.String(length=128), nullable=True),
        sa.Column('consented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_sharing_invitations_inviter_status', 'sharing_invitations', ['inviter_user_id', 'status'])
    op.create_index('ix_sharing_invitations_token', 'sharing_invitations', ['token'])
    op.create_index('ix_sharing_invitations_invitee_email', 'sharing_invitations', ['invitee_email'])

    op.create_table(
        'sharing_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('invitation_id', sa.Integer(), sa.ForeignKey('sharing_invitations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_type', sa.String(length=32), nullable=False),
        sa.Column('payload', sa.LargeBinary(), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_unique_constraint('uq_snapshot_invitation_type', 'sharing_snapshots', ['invitation_id', 'data_type'])
    op.create_index('ix_sharing_snapshots_type_fetched', 'sharing_snapshots', ['data_type', 'fetched_at'])


def downgrade() -> None:
    op.drop_index('ix_sharing_snapshots_type_fetched', table_name='sharing_snapshots')
    op.drop_constraint('uq_snapshot_invitation_type', 'sharing_snapshots', type_='unique')
    op.drop_table('sharing_snapshots')
    op.drop_index('ix_sharing_invitations_inviter_status', table_name='sharing_invitations')
    op.drop_index('ix_sharing_invitations_token', table_name='sharing_invitations')
    op.drop_index('ix_sharing_invitations_invitee_email', table_name='sharing_invitations')
    op.drop_table('sharing_invitations')
