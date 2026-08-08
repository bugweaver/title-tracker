from typing import Any

from litestar import Controller, Request, get
from litestar.di import Provide
from litestar.security.jwt import Token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Title, User, UserTitle
from core.models.db_helper import get_db_session
from core.models.user import subscriptions_table
from titles.schemas import TitleRead

from .schemas import FeedActor, FeedItem


class FeedController(Controller):
    path = "/feed"
    tags = ["Feed"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/")
    async def get_feed(
        self,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
        limit: int = 30,
        offset: int = 0,
    ) -> list[FeedItem]:
        following_ids_stmt = select(subscriptions_table.c.following_id).where(
            subscriptions_table.c.follower_id == request.user.id
        )
        following_result = await db_session.execute(following_ids_stmt)
        following_ids = list(following_result.scalars().all())
        if not following_ids:
            return []

        stmt = (
            select(UserTitle)
            .join(User, User.id == UserTitle.user_id)
            .join(Title, Title.id == UserTitle.title_id)
            .options(
                selectinload(UserTitle.title),
                selectinload(UserTitle.user),
            )
            .where(
                UserTitle.user_id.in_(following_ids),
                Title.parent_title_id.is_(None),
                # Private profiles are only visible to followers; we're already following
            )
            .order_by(UserTitle.updated_at.desc())
            .limit(min(limit, 50))
            .offset(offset)
        )
        result = await db_session.execute(stmt)
        items = result.scalars().unique().all()

        feed: list[FeedItem] = []
        for ut in items:
            is_new = abs((ut.updated_at - ut.created_at).total_seconds()) < 5
            preview = None
            if ut.review_text:
                plain = ut.review_text.replace("<", "").replace(">", "")
                preview = plain[:160] + ("…" if len(plain) > 160 else "")

            feed.append(
                FeedItem(
                    user_title_id=ut.id,
                    event="new" if is_new else "updated",
                    status=ut.status.value if hasattr(ut.status, "value") else str(ut.status),
                    score=ut.score,
                    review_preview=preview,
                    created_at=ut.created_at,
                    updated_at=ut.updated_at,
                    actor=FeedActor.model_validate(ut.user),
                    title=TitleRead.model_validate(ut.title),
                )
            )
        return feed
