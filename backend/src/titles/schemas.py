from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.models.title import TitleCategory, UserTitleStatus


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


class UserTitleRead(UserTitleBase):
    id: int
    user_id: int
    title_id: int
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None = None
    title: TitleRead
    
    model_config = ConfigDict(from_attributes=True)


class UserTitleCreate(UserTitleBase):
    title_id: int


class UserTitleUpdate(UserTitleBase):
    pass
