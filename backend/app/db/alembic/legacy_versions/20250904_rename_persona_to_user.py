from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250904_rename_persona_to_user'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Placeholder revision for environments that already renamed persona->user.
    No-op to align alembic_version.
    """
    pass


def downgrade():
    # No-op
    pass
