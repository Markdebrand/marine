"""create remaining application tables

Revision ID: 0003_create_remaining_tables
Revises: 20251016_spatial
Create Date: 2025-10-16 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003_create_remaining_tables'
down_revision = '20251016_spatial'
branch_labels = None
depends_on = None


def upgrade():
    # Users
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(16), nullable=False, server_default='user'),
        sa.Column('is_superadmin', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('odoo_lead_id', sa.String(64)),
        sa.Column('odoo_partner_id', sa.String(64)),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('phone', sa.String(50)),
        sa.Column('company', sa.String(255)),
        sa.Column('website', sa.String(255)),
        sa.Column('bio', sa.String(1024)),
        sa.Column('last_profile_update_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_user_email', 'user', ['email'])

    # Session tokens
    op.create_table(
        'session_tokens',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(128), nullable=False),
        sa.Column('user_agent', sa.String(255)),
        sa.Column('ip', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True)),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('revoke_reason', sa.String(255)),
        sa.Column('active_seconds', sa.Integer),
    )

    # RBAC: roles, permissions, role_permissions, user_roles
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('slug', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('slug', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', sa.Integer, sa.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Plans & subscriptions
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000)),
        sa.Column('support', sa.String(20), nullable=False),
        sa.Column('features', postgresql.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_id', sa.Integer, sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('cancel_at', sa.DateTime(timezone=True)),
        sa.Column('canceled_at', sa.DateTime(timezone=True)),
        sa.Column('trial_end', sa.DateTime(timezone=True)),
        sa.Column('add_ons', postgresql.JSON, nullable=True),
    )

    # Usage counters
    op.create_table(
        'usage_counters',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('subscription_id', sa.Integer, sa.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feature_key', sa.String(64), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Releases and sections
    op.create_table(
        'releases',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(50), nullable=False),
        sa.Column('version', sa.String(32), nullable=False),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('short_description', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'release_sections',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('release_id', sa.Integer, sa.ForeignKey('releases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('position', sa.Integer, nullable=False, server_default='0'),
    )

    # Contact and form_pending
    op.create_table(
        'contact_requests',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(32)),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('job_title', sa.String(150), nullable=False),
        sa.Column('employees', sa.String(50), nullable=False),
        sa.Column('industry', sa.String(150), nullable=False),
        sa.Column('subscription', postgresql.JSON, nullable=False),
        sa.Column('geographic', sa.String(150), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='new'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'form_pending',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(32)),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('job_title', sa.String(150), nullable=False),
        sa.Column('employees', sa.String(50), nullable=False),
        sa.Column('industry', sa.String(150), nullable=False),
        sa.Column('subscription', postgresql.JSON, nullable=False),
        sa.Column('geographic', sa.String(150), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Activation tokens
    op.create_table(
        'activation_tokens',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True)),
        sa.Column('revoked', sa.Boolean, nullable=False, server_default=sa.text('false')),
    )

    # User preferences
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', postgresql.JSON, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ResUser and extras already exist (res_user created by earlier migration if present)


def downgrade():
    # Drop in reverse order
    op.drop_table('user_preferences')
    op.drop_table('activation_tokens')
    op.drop_table('form_pending')
    op.drop_table('contact_requests')
    op.drop_table('release_sections')
    op.drop_table('releases')
    op.drop_table('usage_counters')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('session_tokens')
    op.drop_index('ix_user_email', table_name='user')
    op.drop_table('user')
