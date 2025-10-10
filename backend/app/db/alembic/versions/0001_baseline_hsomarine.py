"""empty migration - baseline for HSOMarine"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_baseline_hsomarine'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Baseline migration - no operations."""
    pass


def downgrade() -> None:
    """Baseline downgrade - no operations."""
    pass

