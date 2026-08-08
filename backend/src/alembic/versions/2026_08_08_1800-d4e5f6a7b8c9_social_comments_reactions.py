"""social_comments_reactions

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
Create Date: 2026-08-08 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_comments",
        sa.Column("user_title_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_title_id"],
            ["user_titles.id"],
            name=op.f("fk_review_comments_user_title_id_user_titles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_review_comments_author_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_comments")),
    )
    op.create_index(
        op.f("ix_review_comments_user_title_id"),
        "review_comments",
        ["user_title_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_review_comments_author_id"),
        "review_comments",
        ["author_id"],
        unique=False,
    )

    op.create_table(
        "review_reactions",
        sa.Column("user_title_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_title_id"],
            ["user_titles.id"],
            name=op.f("fk_review_reactions_user_title_id_user_titles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_review_reactions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_reactions")),
        sa.UniqueConstraint("user_title_id", "user_id", name="uq_review_reaction"),
    )
    op.create_index(
        op.f("ix_review_reactions_user_title_id"),
        "review_reactions",
        ["user_title_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_review_reactions_user_id"),
        "review_reactions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_review_reactions_user_id"), table_name="review_reactions")
    op.drop_index(op.f("ix_review_reactions_user_title_id"), table_name="review_reactions")
    op.drop_table("review_reactions")
    op.drop_index(op.f("ix_review_comments_author_id"), table_name="review_comments")
    op.drop_index(op.f("ix_review_comments_user_title_id"), table_name="review_comments")
    op.drop_table("review_comments")
