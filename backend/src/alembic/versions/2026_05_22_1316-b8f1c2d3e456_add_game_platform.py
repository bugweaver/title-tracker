"""add_game_platform

Revision ID: b8f1c2d3e456
Revises: a7c4d8e9f123
Create Date: 2026-05-22 13:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8f1c2d3e456'
down_revision: Union[str, Sequence[str], None] = 'a7c4d8e9f123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


game_platform_enum = sa.Enum(
    'PC',
    'PLAYSTATION',
    'XBOX',
    'NINTENDO',
    name='gameplatform',
)


def upgrade() -> None:
    """Upgrade schema."""
    game_platform_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'user_titles',
        sa.Column('game_platform', game_platform_enum, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_titles', 'game_platform')
    game_platform_enum.drop(op.get_bind(), checkfirst=True)
