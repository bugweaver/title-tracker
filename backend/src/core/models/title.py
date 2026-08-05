from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint, func, Float, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import IntIdPkMixin

if TYPE_CHECKING:
    from .user import User
    from .screenshot import TitleScreenshot
    from .season import TitleSeason, UserTitleSeason


class TitleCategory(str, Enum):
    GAME = "game"
    MOVIE = "movie"
    SERIES = "series"
    ANIME = "anime"
    MANGA = "manga"
    COMICS = "comics"
    BOOK = "book"


class UserTitleStatus(str, Enum):
    COMPLETED = "completed"
    PLAYING = "playing"  # For games
    WATCHING = "watching"  # For movies/series/anime/manga/comics/books (Читаю)
    DROPPED = "dropped"
    PLANNED = "planned"
    ON_HOLD = "on_hold"


class GamePlatform(str, Enum):
    PC = "PC"
    PLAYSTATION = "Playstation"
    XBOX = "Xbox"
    NINTENDO = "Nintendo"


class Title(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[TitleCategory] = mapped_column(nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True) # IGDB ID, TMDB ID etc.
    
    # Metadata
    cover_image: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(String(1000))
    release_year: Mapped[int | None] = mapped_column()
    genres: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    seasons: Mapped[list["TitleSeason"]] = relationship(
        "TitleSeason",
        back_populates="title",
        cascade="all, delete-orphan",
        order_by="TitleSeason.season_number",
        lazy="selectin",
    )


class UserTitle(IntIdPkMixin, Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[UserTitleStatus] = mapped_column(nullable=False, default=UserTitleStatus.PLANNED)
    score: Mapped[float | None] = mapped_column(Float)  # 1.0-10.0
    avg_score: Mapped[float | None] = mapped_column(Float)
    score_is_manual: Mapped[bool] = mapped_column(default=False, server_default="false")
    review_text: Mapped[str | None] = mapped_column(Text)
    is_spoiler: Mapped[bool] = mapped_column(default=False, server_default="false")
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    times_completed: Mapped[int] = mapped_column(default=0, server_default="0")
    is_completed_100_percent: Mapped[bool] = mapped_column(default=False, server_default="false")
    game_platform: Mapped[GamePlatform | None] = mapped_column(nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", backref="user_titles")
    title: Mapped["Title"] = relationship("Title")
    screenshots: Mapped[list["TitleScreenshot"]] = relationship(
        "TitleScreenshot",
        backref="user_title",
        cascade="all, delete-orphan",
        order_by="TitleScreenshot.position",
        lazy="selectin",
    )
    seasons: Mapped[list["UserTitleSeason"]] = relationship(
        "UserTitleSeason",
        back_populates="user_title",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "title_id", name="uq_user_title"),
    )
