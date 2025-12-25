"""Add report schedules table

Revision ID: 20250309_add_report_schedules
Revises: 20250308_add_user_language_preferences
Create Date: 2025-03-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '20250309_add_report_schedules'
down_revision = '20250308_add_user_language_preferences'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create report_schedules table for scheduled report generation."""
    op.create_table(
        'report_schedules',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('parameters', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('email_recipients', JSONB, nullable=True),
        sa.Column('notify_on_completion', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for efficient querying
    op.create_index('ix_report_schedules_user_id', 'report_schedules', ['user_id'])
    op.create_index('ix_report_schedules_company_id', 'report_schedules', ['company_id'])
    op.create_index('ix_report_schedules_next_run_at', 'report_schedules', ['next_run_at'])
    op.create_index('ix_report_schedules_is_active', 'report_schedules', ['is_active'])

    # Create schedule execution history table
    op.create_table(
        'schedule_executions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('schedule_id', sa.Integer(), sa.ForeignKey('report_schedules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_id', sa.Integer(), sa.ForeignKey('reports.id'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for schedule execution history
    op.create_index('ix_schedule_executions_schedule_id', 'schedule_executions', ['schedule_id'])
    op.create_index('ix_schedule_executions_started_at', 'schedule_executions', ['started_at'])


def downgrade() -> None:
    """Drop report schedules and execution history tables."""
    op.drop_index('ix_schedule_executions_started_at', 'schedule_executions')
    op.drop_index('ix_schedule_executions_schedule_id', 'schedule_executions')
    op.drop_table('schedule_executions')

    op.drop_index('ix_report_schedules_is_active', 'report_schedules')
    op.drop_index('ix_report_schedules_next_run_at', 'report_schedules')
    op.drop_index('ix_report_schedules_company_id', 'report_schedules')
    op.drop_index('ix_report_schedules_user_id', 'report_schedules')
    op.drop_table('report_schedules')
