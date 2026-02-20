from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import IntIdPkMixin

if TYPE_CHECKING:
    from .user import User
    from .title import UserTitle


class NotificationType(str, Enum):
    NEW_TITLE = "new_title"
    TITLE_UPDATED = "title_updated"
    NEW_FOLLOWER = "new_follower"


class Notification(IntIdPkMixin, Base):
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user_title_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_titles.id", ondelete="CASCADE"), nullable=True
    )
    type: Mapped[NotificationType] = mapped_column(
        String(50), nullable=False, default=NotificationType.NEW_TITLE
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    recipient: Mapped["User"] = relationship(
        "User", foreign_keys=[recipient_id], lazy="selectin"
    )
    actor: Mapped["User"] = relationship(
        "User", foreign_keys=[actor_id], lazy="selectin"
    )
    user_title: Mapped["UserTitle"] = relationship(
        "UserTitle", lazy="selectin"
    )
