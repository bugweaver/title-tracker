from typing import Literal
from datetime import datetime


from pydantic import BaseModel, Field

from core.models.title import UserTitleStatus
from screenshots.schemas import ScreenshotRead


class AddUserTitleRequest(BaseModel):
    # External Data
    external_id: str
    type: Literal["game", "movie", "tv", "anime"]
    name: str
    cover_url: str | None = None
    release_year: int | None = None
    genres: list[str] = []

    # User Data
    status: UserTitleStatus
    score: float | None = Field(None, ge=1, le=10)
    review_text: str | None = None
    is_spoiler: bool = False
    finished_at: datetime | None = None

    
class UserTitleRead(BaseModel):
    id: int
    user_id: int
    title_id: int
    status: UserTitleStatus
    score: float | None
    is_spoiler: bool
    finished_at: datetime | None
    screenshots: list[ScreenshotRead] = []

