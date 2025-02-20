"""create google_id column and make password None by default

Revision ID: ba7c49c44a96
Revises: e7b6b890ee2f
Create Date: 2025-02-09 08:43:44.792477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba7c49c44a96'
down_revision: Union[str, None] = 'e7b6b890ee2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_id", sa.String(), unique=True, nullable=True))
    op.alter_column("users", "password", existing_type=sa.String, nullable=True)
    pass

def downgrade() -> None:
    op.drop_column("users", "google_id")
    op.alter_column("users", "password", existing_type=sa.String(), nullable=False)
    pass
