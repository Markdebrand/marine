"""Alter release constraints: unique (version, type), section content 250 chars

Revision ID: 20250924_alter_release_constraints
Revises: 20250924_add_release_tables
Create Date: 2025-09-24
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250924_alter_release_constraints'
down_revision = '20250924_add_release_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Drop old index and add unique constraint
    op.drop_index('ix_release_version_type', table_name='releases')
    op.create_index('ix_release_version_type', 'releases', ['version', 'type'], unique=True)
    # Alter content column back to Text (sin límite)
    with op.batch_alter_table('release_sections') as batch_op:
        batch_op.alter_column('content', type_=sa.Text(), existing_type=sa.String(250), nullable=False)

def downgrade():
    # Revert content column to String(250)
    with op.batch_alter_table('release_sections') as batch_op:
        batch_op.alter_column('content', type_=sa.String(250), existing_type=sa.Text(), nullable=False)
    # Drop unique index and restore non-unique
    op.drop_index('ix_release_version_type', table_name='releases')
    op.create_index('ix_release_version_type', 'releases', ['version', 'type'], unique=False)