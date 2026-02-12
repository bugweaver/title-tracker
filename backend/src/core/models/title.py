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


class TitleCategory(str, Enum):
    GAME = "game"
    MOVIE = "movie"
    SERIES = "series"
    ANIME = "anime"


class UserTitleStatus(str, Enum):
    COMPLETED = "completed"
    PLAYING = "playing"  # For games
    WATCHING = "watching"  # For movies/series/anime
    DROPPED = "dropped"
    PLANNED = "planned"
    ON_HOLD = "on_hold"


class Title(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[TitleCategory] = mapped_column(nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True) # IGDB ID, TMDB ID etc.
    
    # Metadata
    cover_image: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(String(1000))
    release_year: Mapped[int | None] = mapped_column()
    genres: Mapped[list[str] | None] = mapped_column(ARRAY(String))


class UserTitle(IntIdPkMixin, Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[UserTitleStatus] = mapped_column(nullable=False, default=UserTitleStatus.PLANNED)
    score: Mapped[float | None] = mapped_column(Float)  # 1.0-10.0
    review_text: Mapped[str | None] = mapped_column(Text)
    is_spoiler: Mapped[bool] = mapped_column(default=False, server_default="false")
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", backref="user_titles")
    title: Mapped["Title"] = relationship("Title")

    __table_args__ = (
        UniqueConstraint("user_id", "title_id", name="uq_user_title"),
    )
