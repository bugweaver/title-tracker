"""add_game_100_percent_flag

Revision ID: a7c4d8e9f123
Revises: 04bbf33bc74e
Create Date: 2026-05-22 12:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c4d8e9f123'
down_revision: Union[str, Sequence[str], None] = '04bbf33bc74e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'user_titles',
        sa.Column('is_completed_100_percent', sa.Boolean(), server_default='false', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_titles', 'is_completed_100_percent')
