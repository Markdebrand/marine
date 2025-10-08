#
# script.py.mako
#
# Alembic migration script template
#

"""
Revision ID: 44b87bdd408f
Revises: 20250926_01, 20251001_add_sharing
Create Date: 2025-10-01 16:56:56.022519+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44b87bdd408f'
down_revision = ('20250926_01', '20251001_add_sharing')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
