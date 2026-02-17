#
# script.py.mako
#
# Alembic migration script template
#

"""
Revision ID: ed03fcda63ea
Revises: eee07593189e
Create Date: 2026-02-17 19:49:36.295259+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed03fcda63ea'
down_revision = 'eee07593189e'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the flag_old column (was full of null values)
    op.drop_column('marine_vessel', 'flag_old')


def downgrade():
    # Re-add the flag_old column if needed
    op.add_column('marine_vessel', sa.Column('flag_old', sa.VARCHAR(length=64), nullable=True))

