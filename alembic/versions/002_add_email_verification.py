"""Add email verification fields

Revision ID: 002
Revises: 001
Create Date: 2025-01-11 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email verification fields to users table
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    
    # Add indexes for email verification fields
    op.create_index('ix_users_email_verified', 'users', ['is_email_verified'])
    op.create_index('ix_users_verification_token', 'users', ['email_verification_token'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_users_verification_token', 'users')
    op.drop_index('ix_users_email_verified', 'users')
    
    # Remove columns
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'is_email_verified')