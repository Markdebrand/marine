"""add indexes to session_tokens

Revision ID: 20251023_stidx
Revises: 20251016_add_postgis_timescale_and_spatial_columns
Create Date: 2025-10-23 00:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '20251023_stidx'
down_revision = '20251016_spatial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create indexes to accelerate session lookups and revocations
    op.create_index('ix_sessiontoken_token_hash', 'session_tokens', ['token_hash'], unique=False)
    op.create_index('ix_sessiontoken_user_id_revoked', 'session_tokens', ['user_id', 'revoked_at'], unique=False)
    op.create_index('ix_sessiontoken_user_id', 'session_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_sessiontoken_user_id', table_name='session_tokens')
    op.drop_index('ix_sessiontoken_user_id_revoked', table_name='session_tokens')
    op.drop_index('ix_sessiontoken_token_hash', table_name='session_tokens')
