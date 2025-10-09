from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250904_add_usage_counters'
down_revision = '20250904_rename_persona_to_user'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if 'usage_counters' not in tables:
        op.create_table(
            'usage_counters',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False),
            sa.Column('feature_key', sa.String(length=64), nullable=False),
            sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
            sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
            sa.Column('used', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint('subscription_id', 'feature_key', 'period_start', name='uq_usage_period'),
        )

    # Ensure indexes exist
    try:
        existing_idx = {idx.get('name') for idx in insp.get_indexes('usage_counters')}
    except Exception:
        existing_idx = set()
    if 'ix_usage_feature' not in existing_idx:
        try:
            op.create_index('ix_usage_feature', 'usage_counters', ['feature_key'])
        except Exception:
            pass
    if 'ix_usage_subscription' not in existing_idx:
        try:
            op.create_index('ix_usage_subscription', 'usage_counters', ['subscription_id'])
        except Exception:
            pass


def downgrade():
    try:
        op.drop_index('ix_usage_subscription', table_name='usage_counters')
    except Exception:
        pass
    try:
        op.drop_index('ix_usage_feature', table_name='usage_counters')
    except Exception:
        pass
    try:
        op.drop_table('usage_counters')
    except Exception:
        pass
