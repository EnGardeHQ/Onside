"""Add web scraping tables

Revision ID: 20250311_add_scraping_tables
Revises: 20250310_add_search_history
Create Date: 2025-03-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '20250311_add_scraping_tables'
down_revision = '20250310_add_search_history'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables for web scraping functionality."""

    # Create scraped_content table
    op.create_table(
        'scraped_content',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('domain', sa.String(500), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('competitor_id', sa.Integer(), sa.ForeignKey('competitors.id'), nullable=True),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('title', sa.String(1000), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('meta_keywords', sa.Text(), nullable=True),
        sa.Column('screenshot_url', sa.String(2000), nullable=True),
        sa.Column('screenshot_path', sa.String(1000), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),  # SHA-256 hash
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scrape_duration_ms', sa.Float(), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes
    op.create_index('ix_scraped_content_url', 'scraped_content', ['url'])
    op.create_index('ix_scraped_content_domain', 'scraped_content', ['domain'])
    op.create_index('ix_scraped_content_company_id', 'scraped_content', ['company_id'])
    op.create_index('ix_scraped_content_competitor_id', 'scraped_content', ['competitor_id'])
    op.create_index('ix_scraped_content_content_hash', 'scraped_content', ['content_hash'])
    op.create_index('ix_scraped_content_created_at', 'scraped_content', ['created_at'])

    # Create scraping_schedules table
    op.create_table(
        'scraping_schedules',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('competitor_id', sa.Integer(), sa.ForeignKey('competitors.id'), nullable=True),
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('capture_screenshot', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('scraping_config', JSONB, nullable=True),  # Playwright settings, selectors, etc.
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes
    op.create_index('ix_scraping_schedules_url', 'scraping_schedules', ['url'])
    op.create_index('ix_scraping_schedules_is_active', 'scraping_schedules', ['is_active'])
    op.create_index('ix_scraping_schedules_next_run_at', 'scraping_schedules', ['next_run_at'])

    # Create content_changes table for diff tracking
    op.create_table(
        'content_changes',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('old_version_id', sa.Integer(), sa.ForeignKey('scraped_content.id'), nullable=True),
        sa.Column('new_version_id', sa.Integer(), sa.ForeignKey('scraped_content.id'), nullable=False),
        sa.Column('change_type', sa.String(50), nullable=False),  # content, structure, meta, etc.
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('diff_data', JSONB, nullable=True),  # Detailed diff information
        sa.Column('change_percentage', sa.Float(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes
    op.create_index('ix_content_changes_url', 'content_changes', ['url'])
    op.create_index('ix_content_changes_old_version_id', 'content_changes', ['old_version_id'])
    op.create_index('ix_content_changes_new_version_id', 'content_changes', ['new_version_id'])
    op.create_index('ix_content_changes_detected_at', 'content_changes', ['detected_at'])


def downgrade() -> None:
    """Drop web scraping tables."""
    # Drop content_changes table
    op.drop_index('ix_content_changes_detected_at', 'content_changes')
    op.drop_index('ix_content_changes_new_version_id', 'content_changes')
    op.drop_index('ix_content_changes_old_version_id', 'content_changes')
    op.drop_index('ix_content_changes_url', 'content_changes')
    op.drop_table('content_changes')

    # Drop scraping_schedules table
    op.drop_index('ix_scraping_schedules_next_run_at', 'scraping_schedules')
    op.drop_index('ix_scraping_schedules_is_active', 'scraping_schedules')
    op.drop_index('ix_scraping_schedules_url', 'scraping_schedules')
    op.drop_table('scraping_schedules')

    # Drop scraped_content table
    op.drop_index('ix_scraped_content_created_at', 'scraped_content')
    op.drop_index('ix_scraped_content_content_hash', 'scraped_content')
    op.drop_index('ix_scraped_content_competitor_id', 'scraped_content')
    op.drop_index('ix_scraped_content_company_id', 'scraped_content')
    op.drop_index('ix_scraped_content_domain', 'scraped_content')
    op.drop_index('ix_scraped_content_url', 'scraped_content')
    op.drop_table('scraped_content')
