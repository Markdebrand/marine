"""Add is_active and Odoo IDs to user

Revision ID: 20250922_add_is_active_and_odoo_ids
Revises: 20250917_add_activation_tokens_table
Create Date: 2025-09-22
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250922_add_is_active_and_odoo_ids'
down_revision = '20250917_add_activation_tokens_table'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column('odoo_lead_id', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('odoo_partner_id', sa.String(length=64), nullable=True))
    # remove server_default after filling existing rows
    op.execute("UPDATE `user` SET is_active = 1 WHERE is_active IS NULL")
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('is_active', server_default=None)


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('odoo_partner_id')
        batch_op.drop_column('odoo_lead_id')
        batch_op.drop_column('is_active')
