"""add release and release_section tables

Revision ID: 20250924_add_release_tables
Revises: 20250922_add_is_active_and_odoo_ids_to_user
Create Date: 2025-09-24
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250924_add_release_tables'
down_revision = '20250922_add_is_active_and_odoo_ids'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'releases',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(length=50), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('short_description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_release_version_type', 'releases', ['version', 'type'])

    op.create_table(
        'release_sections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('release_id', sa.Integer(), sa.ForeignKey('releases.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default=sa.text('0')),
    )


def downgrade() -> None:
    op.drop_table('release_sections')
    op.drop_index('ix_release_version_type', table_name='releases')
    op.drop_table('releases')
