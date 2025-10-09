from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250904_alter_org_id_nullable_due_diligence_reports'
down_revision = '20250904_add_org_id_due_diligence_reports'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    if 'due_diligence_reports' in tables:
        cols = {c['name']: c for c in insp.get_columns('due_diligence_reports')}
        if 'org_id' in cols:
            nullable = cols['org_id'].get('nullable', True)
            if not nullable:
                try:
                    op.alter_column(
                        'due_diligence_reports',
                        'org_id',
                        existing_type=sa.Integer(),
                        nullable=True,
                    )
                except Exception:
                    # Best-effort; continue even if backend has limitations
                    pass


def downgrade():
    # No-op: we don't want to force org_id back to NOT NULL
    pass
