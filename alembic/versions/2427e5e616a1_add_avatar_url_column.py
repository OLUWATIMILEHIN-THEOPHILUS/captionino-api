"""add avatar url column

Revision ID: 2427e5e616a1
Revises: ba7c49c44a96
Create Date: 2025-02-21 18:25:32.742532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2427e5e616a1'
down_revision: Union[str, None] = 'ba7c49c44a96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.add_column("users", sa.Column("avatar_url", sa.String(), nullable=True))

    pass

def downgrade() -> None:
    
    op.drop_column("users", "avatar_url")

    pass