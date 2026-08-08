from collections import Counter, defaultdict
from typing import Any

from litestar import Controller, Request, get
from litestar.di import Provide
from litestar.security.jwt import Token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Title, User, UserTitle, UserTitleStatus
from core.models.db_helper import get_db_session
from core.models.user import subscriptions_table
from titles.schemas import TitleRead

from .schemas import RecommendationItem, RecommendedByUser


class SocialController(Controller):
    path = "/social"
    tags = ["Social"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/recommendations")
    async def get_recommendations(
        self,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
        limit: int = 20,
    ) -> list[RecommendationItem]:
        me_id = request.user.id

        following_ids_stmt = select(subscriptions_table.c.following_id).where(
            subscriptions_table.c.follower_id == me_id
        )
        following_result = await db_session.execute(following_ids_stmt)
        following_ids = list(following_result.scalars().all())
        if not following_ids:
            return []

        my_titles_stmt = (
            select(UserTitle)
            .options(selectinload(UserTitle.title))
            .where(UserTitle.user_id == me_id)
        )
        my_result = await db_session.execute(my_titles_stmt)
        my_user_titles = list(my_result.scalars().unique().all())
        my_title_ids = {ut.title_id for ut in my_user_titles}

        genre_weights: Counter[str] = Counter()
        for ut in my_user_titles:
            if ut.status != UserTitleStatus.COMPLETED:
                continue
            for genre in ut.title.genres or []:
                genre_weights[genre] += 1

        friends_stmt = (
            select(UserTitle)
            .join(User, User.id == UserTitle.user_id)
            .join(Title, Title.id == UserTitle.title_id)
            .options(
                selectinload(UserTitle.title),
                selectinload(UserTitle.user),
            )
            .where(
                UserTitle.user_id.in_(following_ids),
                UserTitle.status == UserTitleStatus.COMPLETED,
                Title.parent_title_id.is_(None),
            )
        )
        friends_result = await db_session.execute(friends_stmt)
        friend_entries = list(friends_result.scalars().unique().all())

        # title_id -> {score, shared_genres, recommenders}
        scored: dict[int, dict] = {}
        recommenders: dict[int, list[User]] = defaultdict(list)

        for ut in friend_entries:
            if ut.title_id in my_title_ids:
                continue
            title_genres = set(ut.title.genres or [])
            shared = sorted(g for g in title_genres if g in genre_weights)
            # Prefer genre overlap; still surface friend completions without overlap
            genre_score = sum(genre_weights[g] for g in shared)
            friend_bonus = 1.0
            entry = scored.get(ut.title_id)
            if entry is None:
                scored[ut.title_id] = {
                    "title": ut.title,
                    "score": genre_score + friend_bonus,
                    "shared_genres": shared,
                }
                recommenders[ut.title_id] = [ut.user]
            else:
                entry["score"] += friend_bonus + (0.5 * genre_score)
                if len(recommenders[ut.title_id]) < 3 and ut.user not in recommenders[ut.title_id]:
                    recommenders[ut.title_id].append(ut.user)
                # Merge shared genres
                existing = set(entry["shared_genres"])
                entry["shared_genres"] = sorted(existing | set(shared))

        # If user has no completed genres, still recommend popular among friends
        ranked = sorted(
            scored.items(),
            key=lambda pair: (-pair[1]["score"], pair[1]["title"].name.lower()),
        )[: min(limit, 50)]

        return [
            RecommendationItem(
                title=TitleRead.model_validate(data["title"]),
                score=float(data["score"]),
                shared_genres=data["shared_genres"],
                recommended_by=[
                    RecommendedByUser.model_validate(u) for u in recommenders[title_id]
                ],
            )
            for title_id, data in ranked
        ]
