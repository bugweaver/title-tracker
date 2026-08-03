from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import IntIdPkMixin

if TYPE_CHECKING:
    from .user import User
    from .title import UserTitle


class ReviewView(IntIdPkMixin, Base):
    user_title_id: Mapped[int] = mapped_column(
        ForeignKey("user_titles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    viewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    viewed_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    user_title: Mapped["UserTitle"] = relationship("UserTitle", lazy="noload")
    viewer: Mapped["User"] = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_title_id", "viewer_id", name="uq_review_view"),
    )
