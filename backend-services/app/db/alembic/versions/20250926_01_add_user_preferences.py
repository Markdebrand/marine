"""add user_preferences table

Revision ID: 20250926_01
Revises: 
Create Date: 2025-09-26
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250926_01'
# Set to latest existing head revision so we don't create a new independent head
down_revision = '20250924_alter_release_constraints'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if 'user_preferences' not in insp.get_table_names():
        # Create table without explicit index to avoid duplicate creation if re-run
        op.create_table(
            'user_preferences',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
            sa.Column('key', sa.String(length=100), nullable=False),
            sa.Column('value', sa.JSON(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        # Constraints / index
        try:
            op.create_unique_constraint('uq_user_pref_user_key', 'user_preferences', ['user_id', 'key'])
        except Exception:
            pass
        try:
            op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])
        except Exception:
            pass
    else:
        # Table exists (perhaps from earlier partial run). Ensure constraints exist; ignore if already there.
        try:
            op.create_unique_constraint('uq_user_pref_user_key', 'user_preferences', ['user_id', 'key'])
        except Exception:
            pass
        existing_indexes = [ix['name'] for ix in insp.get_indexes('user_preferences')]
        if 'ix_user_preferences_user_id' not in existing_indexes:
            try:
                op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])
            except Exception:
                pass


def downgrade() -> None:
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_constraint('uq_user_pref_user_key', 'user_preferences', type_='unique')
    op.drop_table('user_preferences')
