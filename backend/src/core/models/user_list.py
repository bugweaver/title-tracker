from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import IntIdPkMixin

if TYPE_CHECKING:
    from .user import User
    from .title import UserTitle


class UserList(IntIdPkMixin, Base):
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", lazy="selectin")
    items: Mapped[list["UserListItem"]] = relationship(
        "UserListItem",
        back_populates="user_list",
        cascade="all, delete-orphan",
        order_by="UserListItem.position",
        lazy="selectin",
    )


class UserListItem(IntIdPkMixin, Base):
    list_id: Mapped[int] = mapped_column(
        ForeignKey("user_lists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_title_id: Mapped[int] = mapped_column(
        ForeignKey("user_titles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user_list: Mapped["UserList"] = relationship("UserList", back_populates="items")
    user_title: Mapped["UserTitle"] = relationship("UserTitle", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("list_id", "user_title_id", name="uq_user_list_item"),
    )
