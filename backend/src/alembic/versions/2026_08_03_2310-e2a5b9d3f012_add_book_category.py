"""add_book_category

Revision ID: e2a5b9d3f012
Revises: d1f4a8c2e901
Create Date: 2026-08-03 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e2a5b9d3f012'
down_revision: Union[str, Sequence[str], None] = 'd1f4a8c2e901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE titlecategory ADD VALUE IF NOT EXISTS 'BOOK'")


def downgrade() -> None:
    # Postgres cannot remove enum values safely; leave as no-op.
    pass
