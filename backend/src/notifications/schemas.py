from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActorInfo(BaseModel):
    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TitleInfo(BaseModel):
    id: int
    name: str
    cover_image: str | None = None
    category: str

    model_config = ConfigDict(from_attributes=True)


class NotificationRead(BaseModel):
    id: int
    type: str
    is_read: bool
    created_at: datetime
    user_title_id: int
    actor: ActorInfo
    title: TitleInfo

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    count: int
