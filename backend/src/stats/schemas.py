from pydantic import BaseModel, Field


class NamedCount(BaseModel):
    name: str
    count: int


class MonthCount(BaseModel):
    month: int
    count: int


class DayCount(BaseModel):
    day: int
    count: int


class YearStatsRead(BaseModel):
    year: int
    month: int | None = None
    completed_count: int
    average_score: float | None
    top_genres: list[NamedCount]
    monthly_heatmap: list[MonthCount]
    daily_heatmap: list[DayCount] = Field(default_factory=list)
    by_platform: list[NamedCount]
    by_category: list[NamedCount]
