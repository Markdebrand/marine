from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250904_add_org_id_due_diligence_reports'
down_revision = '20250904_fix_due_diligence_reports_columns'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    if 'due_diligence_reports' in tables:
        cols = {c['name'] for c in insp.get_columns('due_diligence_reports')}
        if 'org_id' not in cols:
            op.add_column('due_diligence_reports', sa.Column('org_id', sa.Integer(), nullable=True))

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    if 'due_diligence_reports' in tables:
        cols = {c['name'] for c in insp.get_columns('due_diligence_reports')}
        if 'org_id' in cols:
            op.drop_column('due_diligence_reports', 'org_id')
