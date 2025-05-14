"""alter models to fix subscription and free_trial logic

Revision ID: 48b19e063aed
Revises: a21d2b98b7b3
Create Date: 2025-04-26 02:27:02.106591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48b19e063aed'
down_revision: Union[str, None] = 'a21d2b98b7b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define enum here for cleaner code.
subscription_status_enum = sa.Enum(
    'FREE', 'ACTIVE', 'EXPIRED', 'PENDING', name='subscriptionstatus'
)



def upgrade() -> None:

    subscription_status_enum.create(op.get_bind())

    op.add_column('users', sa.Column('subscription_status', subscription_status_enum, server_default='FREE', nullable=False))

    op.alter_column('free_trials', 'used_trials', new_column_name='trials_left')

    op.drop_column('subscriptions', 'is_active')
    op.drop_column('subscriptions', 'end_date')

    op.add_column('subscriptions', sa.Column('status', subscription_status_enum, nullable=False))
    op.add_column('subscriptions', sa.Column('exp_date', sa.TIMESTAMP(timezone=True), nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'subscription_status')

    op.drop_column('subscriptions', 'status')
    op.drop_column('subscriptions', 'exp_date')

    op.add_column('subscriptions', sa.Column(
        'is_active', sa.Boolean(), server_default=sa.text('false'), nullable=False
    ))
    op.add_column('subscriptions', sa.Column(
        'end_date', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False
    ))

    op.alter_column('free_trials', 'trials_left', new_column_name='used_trials')

    subscription_status_enum.drop(op.get_bind(), checkfirst=False)