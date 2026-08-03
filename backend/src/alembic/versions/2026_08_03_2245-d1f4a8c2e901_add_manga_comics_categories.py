"""add_manga_comics_categories

Revision ID: d1f4a8c2e901
Revises: c9e3a1b2d789
Create Date: 2026-08-03 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd1f4a8c2e901'
down_revision: Union[str, Sequence[str], None] = 'c9e3a1b2d789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE titlecategory ADD VALUE IF NOT EXISTS 'MANGA'")
    op.execute("ALTER TYPE titlecategory ADD VALUE IF NOT EXISTS 'COMICS'")


def downgrade() -> None:
    # Postgres cannot remove enum values safely; leave as no-op.
    pass
