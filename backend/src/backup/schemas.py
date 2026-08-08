from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from core.models.title import UserTitleStatus, TitleCategory, GamePlatform


class BackupEpisodeItem(BaseModel):
    episode_number: int
    name: Optional[str] = None
    status: UserTitleStatus = UserTitleStatus.PLANNED
    score: Optional[float] = None


class BackupSeasonItem(BaseModel):
    season_number: int
    name: Optional[str] = None
    episode_count: Optional[int] = None
    status: UserTitleStatus = UserTitleStatus.PLANNED
    score: Optional[float] = None
    score_is_manual: bool = False
    review_text: Optional[str] = None
    is_spoiler: bool = False
    episodes_watched: int = 0
    episodes: Optional[List[BackupEpisodeItem]] = None


class BackupDlcItem(BaseModel):
    external_id: Optional[str] = None
    title: str
    poster_url: Optional[str] = None
    release_year: Optional[int] = None
    genres: Optional[List[str]] = []
    status: UserTitleStatus
    score: Optional[float] = None
    review_text: Optional[str] = None
    is_spoiler: bool = False
    finished_at: Optional[datetime] = None
    times_completed: int = 0
    is_completed_100_percent: bool = False
    game_platform: Optional[GamePlatform] = None


class BackupItem(BaseModel):
    # Title Data
    external_id: Optional[str] = None
    type: TitleCategory
    title: str = Field(..., description="Title name")
    poster_url: Optional[str] = None
    release_year: Optional[int] = None
    genres: Optional[List[str]] = []

    # UserTitle Data
    status: UserTitleStatus
    score: Optional[float] = None
    review_text: Optional[str] = None
    is_spoiler: bool = False
    finished_at: Optional[datetime] = None
    times_completed: int = 0
    is_completed_100_percent: bool = False
    game_platform: Optional[GamePlatform] = None
    progress_value: Optional[int] = None
    screenshots: Optional[List[str]] = None

    seasons: Optional[List[BackupSeasonItem]] = None
    dlcs: Optional[List[BackupDlcItem]] = None


class BackupResponse(BaseModel):
    message: str
    processed_count: int
