from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import IntIdPkMixin

if TYPE_CHECKING:
    from .user import User
    from .title import UserTitle


class ReactionType(str, Enum):
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"


class ReviewComment(IntIdPkMixin, Base):
    user_title_id: Mapped[int] = mapped_column(
        ForeignKey("user_titles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    user_title: Mapped["UserTitle"] = relationship("UserTitle", lazy="noload")
    author: Mapped["User"] = relationship("User", lazy="selectin")


class ReviewReaction(IntIdPkMixin, Base):
    user_title_id: Mapped[int] = mapped_column(
        ForeignKey("user_titles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[ReactionType] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user_title: Mapped["UserTitle"] = relationship("UserTitle", lazy="noload")
    user: Mapped["User"] = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_title_id", "user_id", name="uq_review_reaction"),
    )
