"""Add search history tracking

Revision ID: 20250310_add_search_history
Revises: 20250309_add_report_schedules
Create Date: 2025-03-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '20250310_add_search_history'
down_revision = '20250309_add_report_schedules'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create search_history table."""
    op.create_table(
        'search_history',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('search_type', sa.String(50), nullable=False),  # link_search, content_search, etc.
        sa.Column('filters', JSONB, nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('language', sa.String(5), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for efficient querying
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('ix_search_history_company_id', 'search_history', ['company_id'])
    op.create_index('ix_search_history_created_at', 'search_history', ['created_at'])
    op.create_index('ix_search_history_search_type', 'search_history', ['search_type'])

    # Create GIN index for full-text search on query
    op.execute("""
        CREATE INDEX ix_search_history_query_gin
        ON search_history
        USING gin(to_tsvector('english', query))
    """)


def downgrade() -> None:
    """Drop search_history table."""
    op.execute("DROP INDEX IF EXISTS ix_search_history_query_gin")
    op.drop_index('ix_search_history_search_type', 'search_history')
    op.drop_index('ix_search_history_created_at', 'search_history')
    op.drop_index('ix_search_history_company_id', 'search_history')
    op.drop_index('ix_search_history_user_id', 'search_history')
    op.drop_table('search_history')
