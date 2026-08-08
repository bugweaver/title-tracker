from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.models.title import UserTitleStatus
from titles.schemas import TitleRead


class UserListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UserListUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UserListItemCreate(BaseModel):
    user_title_id: int


class UserListReorderRequest(BaseModel):
    user_title_ids: list[int]


class UserListSummary(BaseModel):
    id: int
    name: str
    items_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListItemRead(BaseModel):
    id: int
    user_title_id: int
    position: int
    status: UserTitleStatus
    score: float | None = None
    progress_value: int | None = None
    title: TitleRead

    model_config = ConfigDict(from_attributes=True)


class UserListDetail(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    items: list[UserListItemRead] = []

    model_config = ConfigDict(from_attributes=True)
