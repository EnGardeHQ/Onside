"""Add LLM fallback tracking.

This migration adds support for LLM fallback tracking and chain-of-thought logging
as part of Sprint 4's AI/ML enhancements.

Revision ID: 20250307_add_llm_fallback_tracking
Revises:
Create Date: 2025-03-07 14:58:27.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic
revision = '20250307_add_llm_fallback_tracking'
down_revision = None  # This is the first migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create LLM provider enum type
    op.execute("""
        CREATE TYPE llm_provider AS ENUM (
            'openai',
            'anthropic',
            'cohere',
            'huggingface',
            'fallback'
        )
    """)
    
    # Create fallback reason enum type
    op.execute("""
        CREATE TYPE fallback_reason AS ENUM (
            'timeout',
            'error',
            'low_confidence',
            'invalid_response',
            'rate_limit'
        )
    """)
    
    # Add new columns to reports table
    op.add_column('reports',
        sa.Column('chain_of_thought', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column('reports',
        sa.Column('confidence_score', sa.Float(), nullable=True)
    )
    op.add_column('reports',
        sa.Column('processing_time', sa.Float(), nullable=True)
    )
    op.add_column('reports',
        sa.Column('fallback_count', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column('reports',
        sa.Column('last_fallback_at', sa.DateTime(), nullable=True)
    )
    
    # Create llm_fallbacks table
    op.create_table('llm_fallbacks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('original_provider', sa.Enum('openai', 'anthropic', 'cohere', 'huggingface', 'fallback',
                                             name='llm_provider'), nullable=False),
        sa.Column('fallback_provider', sa.Enum('openai', 'anthropic', 'cohere', 'huggingface', 'fallback',
                                              name='llm_provider'), nullable=False),
        sa.Column('reason', sa.Enum('timeout', 'error', 'low_confidence', 'invalid_response', 'rate_limit',
                                   name='fallback_reason'), nullable=False),
        sa.Column('original_prompt', sa.String(), nullable=False),
        sa.Column('chain_of_thought', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_fallbacks_id'), 'llm_fallbacks', ['id'], unique=False)
    op.create_index(op.f('ix_llm_fallbacks_report_id'), 'llm_fallbacks', ['report_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_llm_fallbacks_report_id'), table_name='llm_fallbacks')
    op.drop_index(op.f('ix_llm_fallbacks_id'), table_name='llm_fallbacks')
    
    # Drop llm_fallbacks table
    op.drop_table('llm_fallbacks')
    
    # Drop columns from reports table
    op.drop_column('reports', 'last_fallback_at')
    op.drop_column('reports', 'fallback_count')
    op.drop_column('reports', 'processing_time')
    op.drop_column('reports', 'confidence_score')
    op.drop_column('reports', 'chain_of_thought')
    
    # Drop enum types
    op.execute('DROP TYPE fallback_reason')
    op.execute('DROP TYPE llm_provider')
