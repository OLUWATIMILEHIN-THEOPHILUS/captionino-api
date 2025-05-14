"""add daily_usage and timezone column

Revision ID: 574e93ec6de8
Revises: 2c91689ae2ae
Create Date: 2025-05-10 00:19:06.660930

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '574e93ec6de8'
down_revision: Union[str, None] = '2c91689ae2ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.add_column('users', sa.Column('daily_usage', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('timezone', sa.String(), nullable=False, server_default='Africa/Lagos'))


def downgrade() -> None:
    
    op.drop_column('users', 'daily_usage')
    op.drop_column('users', 'timezone')
