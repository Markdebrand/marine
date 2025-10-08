from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON

# revision identifiers, used by Alembic.
revision = '20250915_create_contact_requests_table'
down_revision = '20250910_create_plaid_items'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if 'contact_requests' not in tables:
        op.create_table(
            'contact_requests',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('first_name', sa.String(length=100), nullable=False),
            sa.Column('last_name', sa.String(length=100), nullable=False),
            sa.Column('phone', sa.String(length=32), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('company', sa.String(length=255), nullable=False),
            sa.Column('country', sa.String(length=100), nullable=False),
            sa.Column('job_title', sa.String(length=150), nullable=False),
            sa.Column('employees', sa.String(length=50), nullable=False),
            sa.Column('industry', sa.String(length=150), nullable=False),
            sa.Column('subscription', JSON, nullable=False, server_default='[]'),
            sa.Column('geographic', sa.String(length=150), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='new'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        try:
            op.create_index('ix_contact_requests_email_created', 'contact_requests', ['email', 'created_at'])
        except Exception:
            pass


def downgrade():
    try:
        op.drop_index('ix_contact_requests_email_created', table_name='contact_requests')
    except Exception:
        pass
    try:
        op.drop_table('contact_requests')
    except Exception:
        pass
