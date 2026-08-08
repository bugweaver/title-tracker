from calendar import monthrange
from collections import Counter
from typing import Annotated, Any

from litestar import Controller, Request, get
from litestar.di import Provide
from litestar.params import Parameter
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Title, User, UserTitle, UserTitleStatus
from core.models.db_helper import get_db_session
from .schemas import DayCount, MonthCount, NamedCount, YearStatsRead

CATEGORY_LABELS = {
    "game": "Игры",
    "movie": "Фильмы",
    "series": "Сериалы",
    "anime": "Аниме",
    "manga": "Манга",
    "comics": "Комиксы",
    "book": "Книги",
}


class StatsController(Controller):
    path = "/stats"
    tags = ["Stats"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/year")
    async def get_year_stats(
        self,
        request: Request[User, dict, Any],  # type: ignore
        db_session: AsyncSession,
        year: int,
        month: Annotated[int | None, Parameter(required=False, ge=1, le=12)] = None,
    ) -> YearStatsRead:
        stmt = (
            select(UserTitle)
            .join(Title, UserTitle.title_id == Title.id)
            .options(selectinload(UserTitle.title))
            .where(
                UserTitle.user_id == request.user.id,
                UserTitle.status == UserTitleStatus.COMPLETED,
                UserTitle.finished_at.is_not(None),
                extract("year", UserTitle.finished_at) == year,
                Title.parent_title_id.is_(None),
            )
        )
        result = await db_session.execute(stmt)
        year_completed = list(result.scalars().unique().all())

        month_counter: Counter[int] = Counter()
        for ut in year_completed:
            if ut.finished_at:
                month_counter[ut.finished_at.month] += 1

        if month is None:
            completed = year_completed
            daily_heatmap: list[DayCount] = []
        else:
            completed = [
                ut
                for ut in year_completed
                if ut.finished_at and ut.finished_at.month == month
            ]
            day_counter: Counter[int] = Counter()
            for ut in completed:
                if ut.finished_at:
                    day_counter[ut.finished_at.day] += 1
            days_in_month = monthrange(year, month)[1]
            daily_heatmap = [
                DayCount(day=day, count=day_counter.get(day, 0))
                for day in range(1, days_in_month + 1)
            ]

        scores = [ut.score for ut in completed if ut.score is not None]
        average_score = round(sum(scores) / len(scores), 1) if scores else None

        genre_counter: Counter[str] = Counter()
        for ut in completed:
            for genre in ut.title.genres or []:
                if genre:
                    genre_counter[genre] += 1

        platform_counter: Counter[str] = Counter()
        for ut in completed:
            if ut.game_platform is not None:
                platform_counter[ut.game_platform.value] += 1

        category_counter: Counter[str] = Counter()
        for ut in completed:
            category_counter[ut.title.category.value] += 1

        return YearStatsRead(
            year=year,
            month=month,
            completed_count=len(completed),
            average_score=average_score,
            top_genres=[
                NamedCount(name=name, count=count)
                for name, count in genre_counter.most_common(8)
            ],
            monthly_heatmap=[
                MonthCount(month=m, count=month_counter.get(m, 0))
                for m in range(1, 13)
            ],
            daily_heatmap=daily_heatmap,
            by_platform=[
                NamedCount(name=name, count=count)
                for name, count in platform_counter.most_common()
            ],
            by_category=[
                NamedCount(
                    name=CATEGORY_LABELS.get(name, name),
                    count=count,
                )
                for name, count in category_counter.most_common()
            ],
        )
