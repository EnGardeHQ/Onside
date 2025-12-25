"""Add brand analysis tables for En Garde integration

Revision ID: add_brand_analysis
Revises: 20251221_add_external_api_tables
Create Date: 2025-12-23 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = 'add_brand_analysis'
down_revision = '20251221_add_external_api_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables for En Garde brand analysis integration."""

    # Create brand_analysis_jobs table
    op.create_table(
        'brand_analysis_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('questionnaire', JSONB, nullable=False),
        sa.Column('status', sa.String(50), nullable=False),  # initiated, crawling, analyzing, processing, completed, failed
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),  # 0-100
        sa.Column('results', JSONB, nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    # Create indexes for brand_analysis_jobs
    op.create_index('ix_brand_analysis_jobs_user_id', 'brand_analysis_jobs', ['user_id'])
    op.create_index('ix_brand_analysis_jobs_status', 'brand_analysis_jobs', ['status'])
    op.create_index('ix_brand_analysis_jobs_created_at', 'brand_analysis_jobs', ['created_at'])

    # Create discovered_keywords table
    op.create_table(
        'discovered_keywords',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('brand_analysis_jobs.id'), nullable=False),
        sa.Column('keyword', sa.Text(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),  # website_content, serp_analysis, nlp_extraction
        sa.Column('search_volume', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.Float(), nullable=True),  # 0-100
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='0.0'),  # 0-1
        sa.Column('current_ranking', sa.Integer(), nullable=True),
        sa.Column('serp_features', JSONB, nullable=True),
        sa.Column('confirmed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for discovered_keywords
    op.create_index('ix_discovered_keywords_job_id', 'discovered_keywords', ['job_id'])
    op.create_index('ix_discovered_keywords_confirmed', 'discovered_keywords', ['confirmed'])
    op.create_index('ix_discovered_keywords_relevance_score', 'discovered_keywords', ['relevance_score'])

    # Create identified_competitors table
    op.create_table(
        'identified_competitors',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('brand_analysis_jobs.id'), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='0.0'),  # 0-1
        sa.Column('category', sa.String(50), nullable=False, server_default='secondary'),  # primary, secondary, emerging, niche
        sa.Column('overlap_percentage', sa.Float(), nullable=True),
        sa.Column('keyword_overlap', JSONB, nullable=True),
        sa.Column('content_similarity', sa.Float(), nullable=True),
        sa.Column('confirmed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for identified_competitors
    op.create_index('ix_identified_competitors_job_id', 'identified_competitors', ['job_id'])
    op.create_index('ix_identified_competitors_confirmed', 'identified_competitors', ['confirmed'])
    op.create_index('ix_identified_competitors_relevance_score', 'identified_competitors', ['relevance_score'])
    op.create_index('ix_identified_competitors_domain', 'identified_competitors', ['domain'])

    # Create content_opportunities table
    op.create_table(
        'content_opportunities',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('brand_analysis_jobs.id'), nullable=False),
        sa.Column('topic', sa.Text(), nullable=False),
        sa.Column('gap_type', sa.String(50), nullable=False),  # missing_content, weak_content, competitor_strength
        sa.Column('traffic_potential', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.Float(), nullable=True),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),  # high, medium, low
        sa.Column('recommended_format', sa.String(100), nullable=True),  # blog, guide, video, infographic
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for content_opportunities
    op.create_index('ix_content_opportunities_job_id', 'content_opportunities', ['job_id'])
    op.create_index('ix_content_opportunities_priority', 'content_opportunities', ['priority'])


def downgrade() -> None:
    """Drop brand analysis tables."""

    # Drop content_opportunities table
    op.drop_index('ix_content_opportunities_priority', 'content_opportunities')
    op.drop_index('ix_content_opportunities_job_id', 'content_opportunities')
    op.drop_table('content_opportunities')

    # Drop identified_competitors table
    op.drop_index('ix_identified_competitors_domain', 'identified_competitors')
    op.drop_index('ix_identified_competitors_relevance_score', 'identified_competitors')
    op.drop_index('ix_identified_competitors_confirmed', 'identified_competitors')
    op.drop_index('ix_identified_competitors_job_id', 'identified_competitors')
    op.drop_table('identified_competitors')

    # Drop discovered_keywords table
    op.drop_index('ix_discovered_keywords_relevance_score', 'discovered_keywords')
    op.drop_index('ix_discovered_keywords_confirmed', 'discovered_keywords')
    op.drop_index('ix_discovered_keywords_job_id', 'discovered_keywords')
    op.drop_table('discovered_keywords')

    # Drop brand_analysis_jobs table
    op.drop_index('ix_brand_analysis_jobs_created_at', 'brand_analysis_jobs')
    op.drop_index('ix_brand_analysis_jobs_status', 'brand_analysis_jobs')
    op.drop_index('ix_brand_analysis_jobs_user_id', 'brand_analysis_jobs')
    op.drop_table('brand_analysis_jobs')
