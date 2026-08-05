from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import IntIdPkMixin
from .title import UserTitleStatus

if TYPE_CHECKING:
    from .title import Title, UserTitle


class TitleSeason(IntIdPkMixin, Base):
    title_id: Mapped[int] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    season_number: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    episode_count: Mapped[int | None] = mapped_column(nullable=True)

    title: Mapped["Title"] = relationship("Title", back_populates="seasons")
    episodes: Mapped[list["TitleEpisode"]] = relationship(
        "TitleEpisode",
        back_populates="season",
        cascade="all, delete-orphan",
        order_by="TitleEpisode.episode_number",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("title_id", "season_number", name="uq_title_season"),
    )


class TitleEpisode(IntIdPkMixin, Base):
    title_season_id: Mapped[int] = mapped_column(
        ForeignKey("title_seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    episode_number: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str | None] = mapped_column(String(512), nullable=True)

    season: Mapped["TitleSeason"] = relationship("TitleSeason", back_populates="episodes")

    __table_args__ = (
        UniqueConstraint("title_season_id", "episode_number", name="uq_title_episode"),
    )


class UserTitleSeason(IntIdPkMixin, Base):
    user_title_id: Mapped[int] = mapped_column(
        ForeignKey("user_titles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title_season_id: Mapped[int] = mapped_column(
        ForeignKey("title_seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[UserTitleStatus] = mapped_column(
        nullable=False, default=UserTitleStatus.PLANNED
    )
    score: Mapped[float | None] = mapped_column(Float)
    avg_score: Mapped[float | None] = mapped_column(Float)
    score_is_manual: Mapped[bool] = mapped_column(default=False, server_default="false")
    review_text: Mapped[str | None] = mapped_column(Text)
    is_spoiler: Mapped[bool] = mapped_column(default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    user_title: Mapped["UserTitle"] = relationship(
        "UserTitle", back_populates="seasons"
    )
    title_season: Mapped["TitleSeason"] = relationship("TitleSeason")
    episodes: Mapped[list["UserTitleEpisode"]] = relationship(
        "UserTitleEpisode",
        back_populates="user_title_season",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_title_id", "title_season_id", name="uq_user_title_season"
        ),
    )


class UserTitleEpisode(IntIdPkMixin, Base):
    user_title_season_id: Mapped[int] = mapped_column(
        ForeignKey("user_title_seasons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title_episode_id: Mapped[int] = mapped_column(
        ForeignKey("title_episodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[UserTitleStatus] = mapped_column(
        nullable=False, default=UserTitleStatus.PLANNED
    )
    score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    user_title_season: Mapped["UserTitleSeason"] = relationship(
        "UserTitleSeason", back_populates="episodes"
    )
    title_episode: Mapped["TitleEpisode"] = relationship("TitleEpisode")

    __table_args__ = (
        UniqueConstraint(
            "user_title_season_id",
            "title_episode_id",
            name="uq_user_title_episode",
        ),
    )
