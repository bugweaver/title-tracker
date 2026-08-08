from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from titles.schemas import TitleRead


class FeedActor(BaseModel):
    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FeedItem(BaseModel):
    user_title_id: int
    event: Literal["new", "updated"]
    status: str
    score: float | None = None
    review_preview: str | None = None
    created_at: datetime
    updated_at: datetime
    actor: FeedActor
    title: TitleRead
