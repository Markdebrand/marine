from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250904_fix_due_diligence_reports_columns'
down_revision = '20250904_create_due_diligence_reports'
branch_labels = None
depends_on = None


def _col_exists(insp, table: str, column: str) -> bool:
    try:
        cols = {c['name'] for c in insp.get_columns(table)}
        return column in cols
    except Exception:
        return False


def _idx_exists(insp, table: str, name: str) -> bool:
    try:
        idx = {i['name'] for i in insp.get_indexes(table)}
        return name in idx
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if 'due_diligence_reports' not in tables:
        # Safety: if table vanished, (re)create minimal structure
        op.create_table(
            'due_diligence_reports',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        )
        insp = sa.inspect(bind)

    # Add missing columns
    add_specs = [
        ('owner_id', sa.Integer(), {'nullable': False}),
        ('created_by', sa.Integer(), {'nullable': True}),
        ('title', sa.String(length=255), {'nullable': False, 'server_default': ''}),
        ('status', sa.String(length=16), {'nullable': False, 'server_default': 'draft'}),
        ('content', sa.JSON(), {}),
        ('created_at', sa.DateTime(timezone=True), {'server_default': sa.func.now(), 'nullable': False}),
        ('completed_at', sa.DateTime(timezone=True), {}),
    ]
    for name, typ, kwargs in add_specs:
        if not _col_exists(insp, 'due_diligence_reports', name):
            op.add_column('due_diligence_reports', sa.Column(name, typ, **kwargs))

    # FKs (best effort)
    try:
        # Note: some backends need named constraints to drop later; we let DB generate names
        if not any('owner_id' in fk.get('constrained_columns', []) for fk in insp.get_foreign_keys('due_diligence_reports')):
            op.create_foreign_key(None, 'due_diligence_reports', 'user', ['owner_id'], ['id'], ondelete='CASCADE')
    except Exception:
        pass
    try:
        if not any('created_by' in fk.get('constrained_columns', []) for fk in insp.get_foreign_keys('due_diligence_reports')):
            op.create_foreign_key(None, 'due_diligence_reports', 'user', ['created_by'], ['id'], ondelete='SET NULL')
    except Exception:
        pass

    # Indexes
    if not _idx_exists(insp, 'due_diligence_reports', 'ix_due_reports_owner'):
        try:
            op.create_index('ix_due_reports_owner', 'due_diligence_reports', ['owner_id'])
        except Exception:
            pass
    if not _idx_exists(insp, 'due_diligence_reports', 'ix_due_reports_status'):
        try:
            op.create_index('ix_due_reports_status', 'due_diligence_reports', ['status'])
        except Exception:
            pass


def downgrade():
    # Best-effort drop of indexes only; avoid dropping columns blindly
    try:
        op.drop_index('ix_due_reports_status', table_name='due_diligence_reports')
    except Exception:
        pass
    try:
        op.drop_index('ix_due_reports_owner', table_name='due_diligence_reports')
    except Exception:
        pass
