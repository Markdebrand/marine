"""cleanup legacy plaid and due diligence artifacts for HSO Marine

Revision ID: 20251009_cleanup_legacy
Revises: c18f105a0c25
Create Date: 2025-10-09
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251009_cleanup_legacy'
down_revision = 'c18f105a0c25'
branch_labels = None
depends_on = None


def _table_exists(insp, name: str) -> bool:
    try:
        return name in set(insp.get_table_names())
    except Exception:
        return False


def _col_exists(insp, table: str, column: str) -> bool:
    try:
        return column in {c['name'] for c in insp.get_columns(table)}
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Drop legacy plaid tables if present
    if _table_exists(insp, 'plaid_items'):
        try:
            op.drop_index('ix_plaid_items_user_created', table_name='plaid_items')
        except Exception:
            pass
        try:
            op.drop_table('plaid_items')
        except Exception:
            pass

    if _table_exists(insp, 'plaid_identity_verifications'):
        for idx in (
            'ix_plaid_idv_user_status',
            'ix_plaid_identity_verifications_status',
            'ix_plaid_identity_verifications_plaid_session_id',
            'ix_plaid_identity_verifications_user_id',
        ):
            try:
                op.drop_index(idx, table_name='plaid_identity_verifications')
            except Exception:
                pass
        try:
            op.drop_table('plaid_identity_verifications')
        except Exception:
            pass

    # Remove plaid_item_id from sharing_invitations if present
    if _table_exists(insp, 'sharing_invitations') and _col_exists(insp, 'sharing_invitations', 'plaid_item_id'):
        try:
            op.drop_column('sharing_invitations', 'plaid_item_id')
        except Exception:
            pass

    # No change to due_diligence tables; they are not used and can be dropped later if desired


def downgrade():
    # Irreversible cleanup; no-op downgrade
    pass
