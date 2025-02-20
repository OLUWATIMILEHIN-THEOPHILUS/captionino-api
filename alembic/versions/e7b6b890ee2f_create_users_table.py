"""create users table

Revision ID: e7b6b890ee2f
Revises: 
Create Date: 2025-02-06 04:03:25.553454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7b6b890ee2f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table("users", 
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True), 
        sa.Column("email", sa.String(), unique=True, nullable=False), 
        sa.Column("password", sa.String(), nullable=False), 
        sa.Column("created", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    pass

def downgrade() -> None:

    op.drop_table("users")

    pass
