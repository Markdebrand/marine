#
# script.py.mako
#
# Alembic migration script template
#

"""
Revision ID: 231aac56d8b8
Revises: 20250904_add_usage_counters, 20250904_fix_subscriptions_columns
Create Date: 2025-09-04 16:27:54.629942+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '231aac56d8b8'
down_revision = ('20250904_add_usage_counters', '20250904_fix_subscriptions_columns')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
