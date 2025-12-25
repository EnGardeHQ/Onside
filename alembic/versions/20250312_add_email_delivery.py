"""Add email delivery tracking

Revision ID: 20250312_add_email_delivery
Revises: 20250311_add_scraping_tables
Create Date: 2025-03-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '20250312_add_email_delivery'
down_revision = '20250311_add_scraping_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables for email delivery tracking."""

    # Create email_recipients table
    op.create_table(
        'email_recipients',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create unique constraint on company_id + email
    op.create_unique_constraint('uq_email_recipients_company_email', 'email_recipients', ['company_id', 'email'])
    op.create_index('ix_email_recipients_company_id', 'email_recipients', ['company_id'])

    # Create email_deliveries table
    op.create_table(
        'email_deliveries',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('report_id', sa.Integer(), sa.ForeignKey('reports.id'), nullable=True),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('attachment_path', sa.String(1000), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),  # queued, sent, failed, bounced
        sa.Column('provider', sa.String(50), nullable=True),  # sendgrid, ses, smtp
        sa.Column('provider_message_id', sa.String(255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('bounced_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes
    op.create_index('ix_email_deliveries_report_id', 'email_deliveries', ['report_id'])
    op.create_index('ix_email_deliveries_recipient_email', 'email_deliveries', ['recipient_email'])
    op.create_index('ix_email_deliveries_status', 'email_deliveries', ['status'])
    op.create_index('ix_email_deliveries_created_at', 'email_deliveries', ['created_at'])


def downgrade() -> None:
    """Drop email delivery tables."""
    # Drop email_deliveries table
    op.drop_index('ix_email_deliveries_created_at', 'email_deliveries')
    op.drop_index('ix_email_deliveries_status', 'email_deliveries')
    op.drop_index('ix_email_deliveries_recipient_email', 'email_deliveries')
    op.drop_index('ix_email_deliveries_report_id', 'email_deliveries')
    op.drop_table('email_deliveries')

    # Drop email_recipients table
    op.drop_index('ix_email_recipients_company_id', 'email_recipients')
    op.drop_constraint('uq_email_recipients_company_email', 'email_recipients', type_='unique')
    op.drop_table('email_recipients')
