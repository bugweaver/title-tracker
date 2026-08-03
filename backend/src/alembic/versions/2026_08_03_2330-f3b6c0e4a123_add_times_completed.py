"""add_times_completed

Revision ID: f3b6c0e4a123
Revises: e2a5b9d3f012
Create Date: 2026-08-03 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3b6c0e4a123'
down_revision: Union[str, Sequence[str], None] = 'e2a5b9d3f012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'user_titles',
        sa.Column('times_completed', sa.Integer(), server_default='0', nullable=False),
    )
    # Existing completed titles count as one completion.
    op.execute(
        """
        UPDATE user_titles
        SET times_completed = 1
        WHERE finished_at IS NOT NULL
           OR status::text IN ('COMPLETED', 'completed')
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_titles', 'times_completed')
