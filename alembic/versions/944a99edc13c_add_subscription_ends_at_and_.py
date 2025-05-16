"""add subscription_ends_at and subscription_renews_at fields to user

Revision ID: 944a99edc13c
Revises: 8c02b5211857
Create Date: 2025-05-16 03:49:12.126786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '944a99edc13c'
down_revision: Union[str, None] = '8c02b5211857'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.add_column('users', sa.Column('subscription_ends_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('users', sa.Column('subscription_renews_at', sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    
    op.drop_column('users', 'subscription_ends_at')
    op.drop_column('users', 'subscription_renews_at')