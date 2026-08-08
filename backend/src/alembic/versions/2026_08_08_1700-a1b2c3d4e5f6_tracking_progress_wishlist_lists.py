"""tracking_progress_wishlist_lists

Revision ID: a1b2c3d4e5f6
Revises: c8d5f0a2e3b1
Create Date: 2026-08-08 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c8d5f0a2e3b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE usertitlestatus ADD VALUE IF NOT EXISTS 'WISHLIST'")

    op.add_column(
        "user_titles",
        sa.Column("progress_value", sa.Integer(), nullable=True),
    )

    op.create_table(
        "user_lists",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_lists_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_lists")),
    )
    op.create_index(op.f("ix_user_lists_user_id"), "user_lists", ["user_id"], unique=False)

    op.create_table(
        "user_list_items",
        sa.Column("list_id", sa.Integer(), nullable=False),
        sa.Column("user_title_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["list_id"],
            ["user_lists.id"],
            name=op.f("fk_user_list_items_list_id_user_lists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_title_id"],
            ["user_titles.id"],
            name=op.f("fk_user_list_items_user_title_id_user_titles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_list_items")),
        sa.UniqueConstraint("list_id", "user_title_id", name="uq_user_list_item"),
    )
    op.create_index(
        op.f("ix_user_list_items_list_id"), "user_list_items", ["list_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_list_items_user_title_id"),
        "user_list_items",
        ["user_title_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_list_items_user_title_id"), table_name="user_list_items")
    op.drop_index(op.f("ix_user_list_items_list_id"), table_name="user_list_items")
    op.drop_table("user_list_items")
    op.drop_index(op.f("ix_user_lists_user_id"), table_name="user_lists")
    op.drop_table("user_lists")
    op.drop_column("user_titles", "progress_value")
    # Postgres cannot remove enum values safely; leave WISHLIST as no-op.
