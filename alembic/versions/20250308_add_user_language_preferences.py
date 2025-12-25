"""Add user language preferences

Revision ID: 20250308_add_user_language_preferences
Revises: 20250307_add_llm_fallback_tracking
Create Date: 2025-03-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250308_add_user_language_preferences'
down_revision = '20250307_add_llm_fallback_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add language preference column to users table."""
    op.add_column('users', sa.Column('preferred_language', sa.String(5), nullable=True, server_default='en'))


def downgrade() -> None:
    """Remove language preference column from users table."""
    op.drop_column('users', 'preferred_language')
