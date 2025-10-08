from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250904_fix_subscriptions_columns'
down_revision = '20250904_rename_persona_to_user'
branch_labels = None
depends_on = None


def _col_exists(insp: sa.engine.reflection.Inspector, table: str, column: str) -> bool:
    try:
        cols = {c['name'] for c in insp.get_columns(table)}
        return column in cols
    except Exception:
        return False


def _idx_exists(insp: sa.engine.reflection.Inspector, table: str, name: str) -> bool:
    try:
        idx = {i['name'] for i in insp.get_indexes(table)}
        return name in idx
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    tables = set(insp.get_table_names())

    if 'subscriptions' not in tables:
        # Create full table if it doesn't exist
        op.create_table(
            'subscriptions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plans.id'), nullable=False),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
            sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('current_period_start', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('current_period_end', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('cancel_at', sa.DateTime(timezone=True)),
            sa.Column('canceled_at', sa.DateTime(timezone=True)),
            sa.Column('trial_end', sa.DateTime(timezone=True)),
            sa.Column('add_ons', sa.JSON(), nullable=True),
        )
        try:
            op.create_index('ix_subscriptions_user_status', 'subscriptions', ['user_id', 'status'])
        except Exception:
            pass
        return

    # Table exists: add any missing columns safely
    # Ensure plan_id column exists first (some older schemas might miss it)
    if not _col_exists(insp, 'subscriptions', 'plan_id'):
        op.add_column('subscriptions', sa.Column('plan_id', sa.Integer(), nullable=True))
        # Try to backfill with a default plan if exists (leave NULL otherwise)
        try:
            op.execute("UPDATE subscriptions SET plan_id = (SELECT id FROM plans ORDER BY id LIMIT 1) WHERE plan_id IS NULL")
        except Exception:
            pass
        # Add FK (ignore if fails)
        try:
            op.create_foreign_key(None, 'subscriptions', 'plans', ['plan_id'], ['id'])
        except Exception:
            pass

    # Add missing datetime/json columns
    add_specs = [
        ('started_at', sa.DateTime(timezone=True), {'server_default': sa.text('CURRENT_TIMESTAMP'), 'nullable': False}),
        ('current_period_start', sa.DateTime(timezone=True), {'server_default': sa.text('CURRENT_TIMESTAMP'), 'nullable': False}),
        ('current_period_end', sa.DateTime(timezone=True), {'server_default': sa.text('CURRENT_TIMESTAMP'), 'nullable': False}),
        ('cancel_at', sa.DateTime(timezone=True), {}),
        ('canceled_at', sa.DateTime(timezone=True), {}),
        ('trial_end', sa.DateTime(timezone=True), {}),
        ('add_ons', sa.JSON(), {'nullable': True}),
    ]
    for name, typ, kwargs in add_specs:
        if not _col_exists(insp, 'subscriptions', name):
            op.add_column('subscriptions', sa.Column(name, typ, **kwargs))

    # Ensure index on (user_id, status)
    if not _idx_exists(insp, 'subscriptions', 'ix_subscriptions_user_status'):
        try:
            op.create_index('ix_subscriptions_user_status', 'subscriptions', ['user_id', 'status'])
        except Exception:
            pass


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if 'subscriptions' not in set(insp.get_table_names()):
        return

    # Drop index if present
    try:
        op.drop_index('ix_subscriptions_user_status', table_name='subscriptions')
    except Exception:
        pass

    # Drop columns (reverse order is safer when DB has constraints)
    for col in ['add_ons', 'trial_end', 'canceled_at', 'cancel_at', 'current_period_end', 'current_period_start', 'started_at']:
        try:
            if any(c['name'] == col for c in insp.get_columns('subscriptions')):
                op.drop_column('subscriptions', col)
        except Exception:
            pass

    # plan_id FK/column revert (optional)
    try:
        # Attempt to drop any FK on plan_id
        fks = [fk for fk in insp.get_foreign_keys('subscriptions') if 'plan_id' in fk.get('constrained_columns', [])]
        for fk in fks:
            name = fk.get('name')
            if name:
                try:
                    op.drop_constraint(name, table_name='subscriptions', type_='foreignkey')
                except Exception:
                    pass
        if _col_exists(insp, 'subscriptions', 'plan_id'):
            op.drop_column('subscriptions', 'plan_id')
    except Exception:
        pass
