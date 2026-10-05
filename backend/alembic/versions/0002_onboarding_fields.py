"""add onboarding fields to profiles and scrape_status to users

Revision ID: 0002_onboarding_fields
Revises: 
Create Date: 2026-10-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002_onboarding_fields'
down_revision = None  # set to previous revision ID if one exists
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users table: add scrape tracking columns ─────────────────────────────
    op.add_column('users', sa.Column('scrape_status', sa.String(), nullable=True, server_default='pending'))
    op.add_column('users', sa.Column('scrape_job_count', sa.Integer(), nullable=True, server_default='0'))

    # ── profiles table: add all new onboarding fields ────────────────────────
    # Step 1
    op.add_column('profiles', sa.Column('full_name', sa.String(), nullable=True))
    op.add_column('profiles', sa.Column('domain', sa.String(), nullable=True))
    op.add_column('profiles', sa.Column('education_level', sa.String(), nullable=True))
    op.add_column('profiles', sa.Column('grad_date', sa.String(), nullable=True))

    # Step 2
    op.add_column('profiles', sa.Column('looking_for', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('profiles', sa.Column('any_field_categories', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('profiles', sa.Column('availability', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('profiles', sa.Column('preferred_max_hours', sa.Integer(), nullable=True))

    # Step 3
    op.add_column('profiles', sa.Column('commute_radius_km', sa.Integer(), nullable=True, server_default='10'))

    # Step 4
    op.add_column('profiles', sa.Column('hour_cap_term', sa.Integer(), nullable=True))
    op.add_column('profiles', sa.Column('hour_cap_break', sa.Integer(), nullable=True))
    op.add_column('profiles', sa.Column('work_rights_confirmed', sa.Boolean(), nullable=True))
    op.add_column('profiles', sa.Column('needs_sponsorship', sa.String(), nullable=True))

    # Step 5
    op.add_column('profiles', sa.Column('comfort_customer_facing', sa.Boolean(), nullable=True))


def downgrade() -> None:
    # Step 5
    op.drop_column('profiles', 'comfort_customer_facing')

    # Step 4
    op.drop_column('profiles', 'needs_sponsorship')
    op.drop_column('profiles', 'work_rights_confirmed')
    op.drop_column('profiles', 'hour_cap_break')
    op.drop_column('profiles', 'hour_cap_term')

    # Step 3
    op.drop_column('profiles', 'commute_radius_km')

    # Step 2
    op.drop_column('profiles', 'preferred_max_hours')
    op.drop_column('profiles', 'availability')
    op.drop_column('profiles', 'any_field_categories')
    op.drop_column('profiles', 'looking_for')

    # Step 1
    op.drop_column('profiles', 'grad_date')
    op.drop_column('profiles', 'education_level')
    op.drop_column('profiles', 'domain')
    op.drop_column('profiles', 'full_name')

    # users
    op.drop_column('users', 'scrape_job_count')
    op.drop_column('users', 'scrape_status')
