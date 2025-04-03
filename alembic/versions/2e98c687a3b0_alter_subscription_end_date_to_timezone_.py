"""alter subscription end_date to timezone-aware

Revision ID: 2e98c687a3b0
Revises: 137f8124c2ce
Create Date: 2025-03-20 04:35:10.740794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e98c687a3b0'
down_revision: Union[str, None] = '137f8124c2ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "subscriptions",
        "end_date",
        type_=sa.TIMESTAMP(timezone=True),
        existing_type=sa.DateTime(),
        nullable=False,
        existing_nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "subscriptions",
        "end_date",
        type_=sa.DateTime(),
        existing_type=sa.TIMESTAMP(timezone=True),
        nullable=True,
        existing_nullable=True
    )

