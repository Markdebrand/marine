"""Drop form_pending table

Revision ID: 20250917_drop_form_pending_table
Revises: 20250917_create_form_pending_table
Create Date: 2025-09-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision = '20250917_drop_form_pending_table'
down_revision = '20250917_create_form_pending_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop index if exists, then table
    try:
        op.drop_index('ix_form_pending_email_created', table_name='form_pending')
    except Exception:
        pass
    op.drop_table('form_pending')


def downgrade() -> None:
    # Recreate table structure if downgrade is needed
    op.create_table(
        'form_pending',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('job_title', sa.String(length=150), nullable=False),
        sa.Column('employees', sa.String(length=50), nullable=False),
        sa.Column('industry', sa.String(length=150), nullable=False),
        sa.Column('subscription', sa.JSON(), nullable=False),
        sa.Column('geographic', sa.String(length=150), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_form_pending')),
    )
    op.create_index('ix_form_pending_email_created', 'form_pending', ['email', 'created_at'], unique=False)
