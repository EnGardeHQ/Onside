"""Add external API data tables.

This migration creates tables for storing data from external APIs:
- gnews_articles: News articles from GNews API
- ipinfo_records: IP/domain geolocation from IPInfo API
- whois_records: Domain WHOIS data from WhoAPI
- api_usage_records: API usage tracking and quota management

Revision ID: 20251221_add_external_api_tables
Revises: 20250307_add_llm_fallback_tracking
Create Date: 2025-12-21
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '20251221_add_external_api_tables'
down_revision = '20250307_add_llm_fallback_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create external API data tables."""

    # Create gnews_articles table
    op.create_table(
        'gnews_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('image_url', sa.String(2048), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_name', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(2048), nullable=True),
        sa.Column('query_term', sa.String(255), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('country', sa.String(10), nullable=True),
        sa.Column('competitor_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['competitor_id'], ['competitors.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_gnews_articles_id', 'gnews_articles', ['id'], unique=False)
    op.create_index('ix_gnews_articles_article_id', 'gnews_articles', ['article_id'], unique=True)
    op.create_index('ix_gnews_articles_published_at', 'gnews_articles', ['published_at'], unique=False)
    op.create_index('ix_gnews_articles_query_term', 'gnews_articles', ['query_term'], unique=False)
    op.create_index('ix_gnews_articles_competitor_id', 'gnews_articles', ['competitor_id'], unique=False)
    op.create_index('ix_gnews_articles_competitor_published', 'gnews_articles', ['competitor_id', 'published_at'], unique=False)
    op.create_index('ix_gnews_articles_query_published', 'gnews_articles', ['query_term', 'published_at'], unique=False)

    # Create ipinfo_records table
    op.create_table(
        'ipinfo_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),  # IPv6 max length
        sa.Column('hostname', sa.String(255), nullable=True),
        sa.Column('city', sa.String(255), nullable=True),
        sa.Column('region', sa.String(255), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('location', sa.JSON(), nullable=True),  # {"lat": float, "lng": float}
        sa.Column('organization', sa.String(500), nullable=True),
        sa.Column('postal', sa.String(20), nullable=True),
        sa.Column('timezone', sa.String(100), nullable=True),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ipinfo_records_id', 'ipinfo_records', ['id'], unique=False)
    op.create_index('ix_ipinfo_records_ip_address', 'ipinfo_records', ['ip_address'], unique=False)
    op.create_index('ix_ipinfo_records_country', 'ipinfo_records', ['country'], unique=False)
    op.create_index('ix_ipinfo_records_domain_id', 'ipinfo_records', ['domain_id'], unique=False)
    op.create_index('ix_ipinfo_records_domain_created', 'ipinfo_records', ['domain_id', 'created_at'], unique=False)
    op.create_index('ix_ipinfo_records_ip_domain', 'ipinfo_records', ['ip_address', 'domain_id'], unique=True)

    # Create whois_records table
    op.create_table(
        'whois_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_name', sa.String(255), nullable=False),
        sa.Column('registrar', sa.String(255), nullable=True),
        sa.Column('registration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('nameservers', sa.JSON(), nullable=True),  # ["ns1.example.com", ...]
        sa.Column('status', sa.JSON(), nullable=True),  # ["clientTransferProhibited", ...]
        sa.Column('dnssec', sa.Boolean(), nullable=True),
        sa.Column('registrant_name', sa.String(255), nullable=True),
        sa.Column('registrant_org', sa.String(255), nullable=True),
        sa.Column('registrant_country', sa.String(2), nullable=True),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_whois_records_id', 'whois_records', ['id'], unique=False)
    op.create_index('ix_whois_records_domain_name', 'whois_records', ['domain_name'], unique=False)
    op.create_index('ix_whois_records_registration_date', 'whois_records', ['registration_date'], unique=False)
    op.create_index('ix_whois_records_expiration_date', 'whois_records', ['expiration_date'], unique=False)
    op.create_index('ix_whois_records_domain_id', 'whois_records', ['domain_id'], unique=False)
    op.create_index('ix_whois_records_domain_updated', 'whois_records', ['domain_id', 'updated_at'], unique=False)
    op.create_index('ix_whois_records_expiration', 'whois_records', ['expiration_date'], unique=False)

    # Create api_usage_records table
    op.create_table(
        'api_usage_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_name', sa.String(100), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_limit', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cost_per_call', sa.Numeric(10, 6), nullable=True),
        sa.Column('total_cost', sa.Numeric(10, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_usage_records_id', 'api_usage_records', ['id'], unique=False)
    op.create_index('ix_api_usage_records_api_name', 'api_usage_records', ['api_name'], unique=False)
    op.create_index('ix_api_usage_records_period_start', 'api_usage_records', ['period_start'], unique=False)
    op.create_index('ix_api_usage_api_period', 'api_usage_records', ['api_name', 'period_start', 'period_end'], unique=False)
    op.create_index('ix_api_usage_created', 'api_usage_records', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop external API data tables."""

    # Drop api_usage_records table and indexes
    op.drop_index('ix_api_usage_created', table_name='api_usage_records')
    op.drop_index('ix_api_usage_api_period', table_name='api_usage_records')
    op.drop_index('ix_api_usage_records_period_start', table_name='api_usage_records')
    op.drop_index('ix_api_usage_records_api_name', table_name='api_usage_records')
    op.drop_index('ix_api_usage_records_id', table_name='api_usage_records')
    op.drop_table('api_usage_records')

    # Drop whois_records table and indexes
    op.drop_index('ix_whois_records_expiration', table_name='whois_records')
    op.drop_index('ix_whois_records_domain_updated', table_name='whois_records')
    op.drop_index('ix_whois_records_domain_id', table_name='whois_records')
    op.drop_index('ix_whois_records_expiration_date', table_name='whois_records')
    op.drop_index('ix_whois_records_registration_date', table_name='whois_records')
    op.drop_index('ix_whois_records_domain_name', table_name='whois_records')
    op.drop_index('ix_whois_records_id', table_name='whois_records')
    op.drop_table('whois_records')

    # Drop ipinfo_records table and indexes
    op.drop_index('ix_ipinfo_records_ip_domain', table_name='ipinfo_records')
    op.drop_index('ix_ipinfo_records_domain_created', table_name='ipinfo_records')
    op.drop_index('ix_ipinfo_records_domain_id', table_name='ipinfo_records')
    op.drop_index('ix_ipinfo_records_country', table_name='ipinfo_records')
    op.drop_index('ix_ipinfo_records_ip_address', table_name='ipinfo_records')
    op.drop_index('ix_ipinfo_records_id', table_name='ipinfo_records')
    op.drop_table('ipinfo_records')

    # Drop gnews_articles table and indexes
    op.drop_index('ix_gnews_articles_query_published', table_name='gnews_articles')
    op.drop_index('ix_gnews_articles_competitor_published', table_name='gnews_articles')
    op.drop_index('ix_gnews_articles_competitor_id', table_name='gnews_articles')
    op.drop_index('ix_gnews_articles_query_term', table_name='gnews_articles')
    op.drop_index('ix_gnews_articles_published_at', table_name='gnews_articles')
    op.drop_index('ix_gnews_articles_article_id', table_name='gnews_articles')
    op.drop_index('ix_gnews_articles_id', table_name='gnews_articles')
    op.drop_table('gnews_articles')
