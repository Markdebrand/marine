"""Drop contact_requests table

Revision ID: 20250917_drop_contact_requests_table
Revises: 20250917_drop_form_pending_table
Create Date: 2025-09-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = '20250917_drop_contact_requests_table'
down_revision = '20250917_drop_form_pending_table'
branch_labels = None
depends_on = None

def upgrade() -> None:
    try:
        op.drop_index('ix_contact_requests_email_created', table_name='contact_requests')
    except Exception:
        pass
    op.drop_table('contact_requests')

def downgrade() -> None:
    op.create_table(
        'contact_requests',
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
        sa.Column('status', sa.String(length=32), nullable=False, server_default='new'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contact_requests')),
    )
    op.create_index('ix_contact_requests_email_created', 'contact_requests', ['email', 'created_at'], unique=False)