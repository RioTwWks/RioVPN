"""add referral system

Revision ID: 002_referral
Revises: 001_initial
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_referral'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add referral system tables and columns."""
    # Add referral columns to users table
    op.add_column(
        'users',
        sa.Column('referral_code', sa.String(length=32), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('referred_by', sa.BigInteger(), nullable=True)
    )
    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)
    op.create_foreign_key(
        'fk_users_referred_by',
        'users', 'users',
        ['referred_by'], ['telegram_id']
    )

    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('referrer_id', sa.BigInteger(), nullable=False),
        sa.Column('referred_id', sa.BigInteger(), nullable=False),
        sa.Column('bonus_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.telegram_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referrals_referrer_id'), 'referrals', ['referrer_id'], unique=False)
    op.create_index(op.f('ix_referrals_referred_id'), 'referrals', ['referred_id'], unique=True)


def downgrade() -> None:
    """Remove referral system."""
    op.drop_index(op.f('ix_referrals_referred_id'), table_name='referrals')
    op.drop_index(op.f('ix_referrals_referrer_id'), table_name='referrals')
    op.drop_table('referrals')
    
    op.drop_constraint('fk_users_referred_by', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_column('users', 'referred_by')
    op.drop_column('users', 'referral_code')
