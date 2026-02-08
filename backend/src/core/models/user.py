from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import IntIdPkMixin

subscriptions_table = Table(
    "subscriptions",
    Base.metadata,
    Column("follower_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "following_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class User(IntIdPkMixin, Base):
    login: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password: Mapped[str] = mapped_column(nullable=False)

    name = mapped_column(String(50))
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(512))

    is_active: Mapped[bool] = mapped_column(default=True)
    is_private: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    followers: Mapped[list["User"]] = relationship(
        "User",
        secondary=subscriptions_table,
        primaryjoin=lambda: User.id == subscriptions_table.c.following_id,
        secondaryjoin=lambda: User.id == subscriptions_table.c.follower_id,
        back_populates="following",
        lazy="selectin",
    )

    following: Mapped[list["User"]] = relationship(
        "User",
        secondary=subscriptions_table,
        primaryjoin=lambda: User.id == subscriptions_table.c.follower_id,
        secondaryjoin=lambda: User.id == subscriptions_table.c.following_id,
        back_populates="followers",
        lazy="selectin",
    )

