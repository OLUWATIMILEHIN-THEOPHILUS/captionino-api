"""add lemonsqueezy customer and subscription id

Revision ID: 8c02b5211857
Revises: 574e93ec6de8
Create Date: 2025-05-14 11:54:04.448568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c02b5211857'
down_revision: Union[str, None] = '574e93ec6de8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.add_column('users', sa.Column('lemonsqueezy_customer_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('lemonsqueezy_subscription_id', sa.String(), nullable=True))


def downgrade() -> None:
    
    op.drop_column('users', 'lemonsqueezy_customer_id')
    op.drop_column('users', 'lemonsqueezy_subscription_id')