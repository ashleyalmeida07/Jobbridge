"""add discovery and careers cache tables; add pay_period and category to jobs

Revision ID: 0003_discovery_tables
Revises: 0002_onboarding_fields
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003_discovery_tables'
down_revision = '0002_onboarding_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── jobs: new columns ────────────────────────────────────────────────────
    op.add_column('jobs', sa.Column('pay_period', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('category', sa.String(), nullable=True))

    # ── scrape_runs table ────────────────────────────────────────────────────
    op.create_table(
        'scrape_runs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending'),
        sa.Column('jobs_found', sa.Integer(), server_default='0'),
        sa.Column('jobs_saved', sa.Integer(), server_default='0'),
        sa.Column('error_msg', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_scrape_runs_source', 'scrape_runs', ['source'])
    op.create_index('ix_scrape_runs_id', 'scrape_runs', ['id'])

    # ── discovered_employers table ───────────────────────────────────────────
    op.create_table(
        'discovered_employers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('osm_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lng', sa.Float(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('brand', sa.String(), nullable=True),
        sa.Column('area_key', sa.String(), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_discovered_employers_id', 'discovered_employers', ['id'])
    op.create_index('ix_discovered_employers_osm_id', 'discovered_employers', ['osm_id'])
    op.create_index('ix_discovered_employers_category', 'discovered_employers', ['category'])
    op.create_index('ix_discovered_employers_area_key', 'discovered_employers', ['area_key'])

    # ── careers_page_cache table ─────────────────────────────────────────────
    op.create_table(
        'careers_page_cache',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('domain', sa.String(), unique=True, nullable=False),
        sa.Column('careers_url', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('method', sa.String(), nullable=True),
        sa.Column('cached_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_careers_page_cache_id', 'careers_page_cache', ['id'])
    op.create_index('ix_careers_page_cache_domain', 'careers_page_cache', ['domain'], unique=True)


def downgrade() -> None:
    op.drop_table('careers_page_cache')
    op.drop_table('discovered_employers')
    op.drop_table('scrape_runs')
    op.drop_column('jobs', 'category')
    op.drop_column('jobs', 'pay_period')
