from typing import Literal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.models.title import GamePlatform, UserTitleStatus
from screenshots.schemas import ScreenshotRead


class AddUserTitleRequest(BaseModel):
    # External Data
    external_id: str
    type: Literal["game", "movie", "tv", "series", "anime", "manga", "comics", "book"]
    name: str
    cover_url: str | None = None
    release_year: int | None = None
    genres: list[str] = []

    # User Data
    status: UserTitleStatus
    score: float | None = Field(None, ge=1, le=10)
    score_is_manual: bool | None = None
    review_text: str | None = None
    is_spoiler: bool = False
    finished_at: datetime | None = None
    is_completed_100_percent: bool = False
    game_platform: GamePlatform | None = None
    increment_completion: bool = False


class UserTitleRead(BaseModel):
    id: int
    user_id: int
    title_id: int
    status: UserTitleStatus
    score: float | None
    avg_score: float | None = None
    score_is_manual: bool = False
    is_spoiler: bool
    finished_at: datetime | None
    times_completed: int
    is_completed_100_percent: bool
    game_platform: GamePlatform | None
    screenshots: list[ScreenshotRead] = []


class UpdateSeasonRequest(BaseModel):
    status: UserTitleStatus | None = None
    score: float | None = Field(None, ge=1, le=10)
    clear_score: bool = False
    review_text: str | None = None
    is_spoiler: bool | None = None


class UpdateEpisodeRequest(BaseModel):
    status: UserTitleStatus | None = None
    score: float | None = Field(None, ge=1, le=10)
    clear_score: bool = False


class EpisodeStructureRead(BaseModel):
    id: int | None = None
    title_episode_id: int
    episode_number: int
    name: str | None = None
    status: UserTitleStatus | None = None
    score: float | None = None

    model_config = ConfigDict(from_attributes=True)


class SeasonStructureRead(BaseModel):
    id: int | None = None
    title_season_id: int
    season_number: int
    name: str | None = None
    episode_count: int | None = None
    status: UserTitleStatus | None = None
    score: float | None = None
    avg_score: float | None = None
    score_is_manual: bool = False
    review_text: str | None = None
    is_spoiler: bool = False
    episodes: list[EpisodeStructureRead] = []
    episodes_loaded: bool = False

    model_config = ConfigDict(from_attributes=True)


class SeriesStructureRead(BaseModel):
    user_title_id: int
    title_id: int
    score: float | None = None
    avg_score: float | None = None
    score_is_manual: bool = False
    status: UserTitleStatus
    review_text: str | None = None
    seasons: list[SeasonStructureRead] = []


class UpdateDlcRequest(BaseModel):
    status: UserTitleStatus | None = None
    score: float | None = Field(None, ge=1, le=10)
    clear_score: bool = False
    review_text: str | None = None
    is_spoiler: bool | None = None


class DlcItemRead(BaseModel):
    title_id: int
    external_id: str | None = None
    name: str
    cover_image: str | None = None
    release_year: int | None = None
    user_title_id: int | None = None
    status: UserTitleStatus | None = None
    score: float | None = None
    review_text: str | None = None
    is_spoiler: bool = False

    model_config = ConfigDict(from_attributes=True)


class GameDlcsRead(BaseModel):
    user_title_id: int
    title_id: int
    dlcs: list[DlcItemRead] = []
