from pydantic import BaseModel, ConfigDict

from titles.schemas import TitleRead


class RecommendedByUser(BaseModel):
    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationItem(BaseModel):
    title: TitleRead
    score: float
    shared_genres: list[str]
    recommended_by: list[RecommendedByUser]
