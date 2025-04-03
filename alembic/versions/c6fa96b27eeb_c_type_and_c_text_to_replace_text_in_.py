"""c_type and c_text to replace text in Caption and created FreeTrial table

Revision ID: c6fa96b27eeb
Revises: 2e98c687a3b0
Create Date: 2025-03-25 18:58:40.669916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6fa96b27eeb'
down_revision: Union[str, None] = '2e98c687a3b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("captions", "text")
    op.add_column("captions", sa.Column("c_text", sa.Text, nullable=False))
    op.add_column("captions", sa.Column("c_type", sa.String, nullable=False))

    op.create_table("free_trials",
        sa.Column("id", sa.UUID(as_uuid=True), index=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete='CASCADE'),
        sa.Column("used_trials", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column("updated", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text("now()"))
    )


def downgrade() -> None:
    op.add_column("captions", sa.Column("text", sa.String(), nullable=False))
    op.drop_column("captions", "c_text")
    op.drop_column("captions", "c_type")

    op.drop_table("free_trials")
