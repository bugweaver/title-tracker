from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.models.title import GamePlatform, TitleCategory, UserTitleStatus
from screenshots.schemas import ScreenshotRead
from users.schemas import UserRead


class TitleBase(BaseModel):
    name: str
    category: TitleCategory
    external_id: str | None = None
    cover_image: str | None = None
    description: str | None = None
    release_year: int | None = None
    genres: list[str] | None = None


class TitleRead(TitleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class TitleCreate(TitleBase):
    pass


class UserTitleBase(BaseModel):
    status: UserTitleStatus
    score: int | float | None = None
    review_text: str | None = None
    game_platform: GamePlatform | None = None


class UserTitleRead(UserTitleBase):
    id: int
    user_id: int
    title_id: int
    is_spoiler: bool = False
    avg_score: float | None = None
    score_is_manual: bool = False
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None = None
    times_completed: int = 0
    is_completed_100_percent: bool = False
    title: TitleRead
    screenshots: list[ScreenshotRead] = []
    view_count: int | None = None
    
    model_config = ConfigDict(from_attributes=True)


class ReviewViewRecordResponse(BaseModel):
    recorded: bool


class ReviewViewsResponse(BaseModel):
    count: int
    viewers: list[UserRead]


class UserTitleCreate(UserTitleBase):
    title_id: int


class UserTitleUpdate(UserTitleBase):
    pass

