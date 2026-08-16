"""replace stripe payment intent id with generic payment fields

Revision ID: 7a1b2c3d4e5f
Revises: 354212d65d03
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7a1b2c3d4e5f'
down_revision: Union[str, None] = '354212d65d03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('orders', 'stripe_payment_intent_id', new_column_name='payment_reference')
    op.add_column('orders', sa.Column('payment_method', sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'payment_method')
    op.alter_column('orders', 'payment_reference', new_column_name='stripe_payment_intent_id')
