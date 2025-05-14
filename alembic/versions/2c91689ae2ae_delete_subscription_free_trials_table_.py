"""delete subscription, free trials table and add trials left field to user

Revision ID: 2c91689ae2ae
Revises: 48b19e063aed
Create Date: 2025-05-02 19:06:12.015078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c91689ae2ae'
down_revision: Union[str, None] = '48b19e063aed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define enum here for cleaner code.
subscription_status_enum = sa.Enum(
    'FREE', 'ACTIVE', 'EXPIRED', 'PENDING', name='subscriptionstatus'
)


def upgrade() -> None:
    
    op.drop_table("subscriptions")
    op.drop_table("free_trials")
    op.drop_column('users', 'subscription_status')

    subscription_status_enum.drop(op.get_bind(), checkfirst=False)

    op.add_column('users', sa.Column('subscription_status', sa.String(), nullable=False, server_default='FREE'))

    op.add_column('users', sa.Column('trials_left', sa.Integer(), nullable=False, server_default='0'))


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

    op.drop_column('users', 'subscription_status')
    subscription_status_enum.create(op.get_bind())

    op.add_column('users', sa.Column('subscription_status', nullable=False, server_default='FREE'))
    op.drop_column('users', 'trials_left')
    