"""add_review_views

Revision ID: c9e3a1b2d789
Revises: b8f1c2d3e456
Create Date: 2026-08-03 12:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9e3a1b2d789'
down_revision: Union[str, Sequence[str], None] = 'b8f1c2d3e456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'review_views',
        sa.Column('user_title_id', sa.Integer(), nullable=False),
        sa.Column('viewer_id', sa.Integer(), nullable=False),
        sa.Column('viewed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_title_id'],
            ['user_titles.id'],
            name=op.f('fk_review_views_user_title_id_user_titles'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['viewer_id'],
            ['users.id'],
            name=op.f('fk_review_views_viewer_id_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_review_views')),
        sa.UniqueConstraint('user_title_id', 'viewer_id', name='uq_review_view'),
    )
    op.create_index(op.f('ix_review_views_user_title_id'), 'review_views', ['user_title_id'], unique=False)
    op.create_index(op.f('ix_review_views_viewer_id'), 'review_views', ['viewer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_review_views_viewer_id'), table_name='review_views')
    op.drop_index(op.f('ix_review_views_user_title_id'), table_name='review_views')
    op.drop_table('review_views')
