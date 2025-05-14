"""create caption and subscription table, and added the relationships to user table

Revision ID: 137f8124c2ce
Revises: 2427e5e616a1
Create Date: 2025-03-19 23:18:45.778239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '137f8124c2ce'
down_revision: Union[str, None] = '2427e5e616a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("captions",
        sa.Column("id", sa.UUID(as_uuid=True), index=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete='CASCADE'),
        sa.Column("created", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column("text", sa.String, nullable=False),
        sa.Column("image_url", sa.String, nullable=False) 
    )
    
    op.create_table("subscriptions",
        sa.Column("id", sa.UUID(as_uuid=True), index=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete='CASCADE'),
        sa.Column("is_active", sa.Boolean, server_default="False", nullable=False),
        sa.Column("start_date", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table("captions")
    op.drop_table("subscriptions")
