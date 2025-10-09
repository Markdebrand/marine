from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON

# revision identifiers, used by Alembic.
revision = '20250904_create_due_diligence_reports'
down_revision = '231aac56d8b8'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if 'due_diligence_reports' not in tables:
        op.create_table(
            'due_diligence_reports',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('status', sa.String(length=16), nullable=False, server_default='draft'),
            sa.Column('content', JSON),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True)),
        )
        try:
            op.create_index('ix_due_reports_owner', 'due_diligence_reports', ['owner_id'])
        except Exception:
            pass
        try:
            op.create_index('ix_due_reports_status', 'due_diligence_reports', ['status'])
        except Exception:
            pass


def downgrade():
    try:
        op.drop_index('ix_due_reports_status', table_name='due_diligence_reports')
    except Exception:
        pass
    try:
        op.drop_index('ix_due_reports_owner', table_name='due_diligence_reports')
    except Exception:
        pass
    try:
        op.drop_table('due_diligence_reports')
    except Exception:
        pass
