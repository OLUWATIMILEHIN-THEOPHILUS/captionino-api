"""delete subscription and free trial table

Revision ID: a21d2b98b7b3
Revises: c6fa96b27eeb
Create Date: 2025-04-03 14:55:23.625651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a21d2b98b7b3'
down_revision: Union[str, None] = 'c6fa96b27eeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("free_trials")


def downgrade() -> None:
    
    op.create_table("subscriptions",
        sa.Column("id", sa.UUID(as_uuid=True), index=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete='CASCADE'),
        sa.Column("is_active", sa.Boolean, server_default="False", nullable=False),
        sa.Column("start_date", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_table("free_trials",
        sa.Column("id", sa.UUID(as_uuid=True), index=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete='CASCADE'),
        sa.Column("used_trials", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column("updated", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text("now()"))
    )