#
# script.py.mako
#
# Alembic migration script template
#

"""
Revision ID: c18f105a0c25
Revises: 20251001_add_snapshot_history, 44b87bdd408f
Create Date: 2025-10-01 18:10:28.260108+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c18f105a0c25'
down_revision = ('20251001_add_snapshot_history', '44b87bdd408f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
