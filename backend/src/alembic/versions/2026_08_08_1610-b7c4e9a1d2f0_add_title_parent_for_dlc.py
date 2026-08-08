"""add_title_parent_for_dlc

Revision ID: b7c4e9a1d2f0
Revises: 853f3b3562c8
Create Date: 2026-08-08 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c4e9a1d2f0'
down_revision: Union[str, Sequence[str], None] = '853f3b3562c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'titles',
        sa.Column('parent_title_id', sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f('ix_titles_parent_title_id'),
        'titles',
        ['parent_title_id'],
        unique=False,
    )
    op.create_foreign_key(
        op.f('fk_titles_parent_title_id_titles'),
        'titles',
        'titles',
        ['parent_title_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f('fk_titles_parent_title_id_titles'),
        'titles',
        type_='foreignkey',
    )
    op.drop_index(op.f('ix_titles_parent_title_id'), table_name='titles')
    op.drop_column('titles', 'parent_title_id')
