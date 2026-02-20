from typing import Any
from datetime import datetime

from litestar import Controller, post, Request
from litestar.di import Provide
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User, Title, UserTitle, TitleCategory, UserTitleStatus
from core.models.notification import Notification, NotificationType
from core.models.user import subscriptions_table
from core.models.db_helper import get_db_session
from .schemas import AddUserTitleRequest, UserTitleRead


class UserTitlesController(Controller):
    path = "/user-titles"
    tags = ["User Titles"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @post("/")
    async def add_user_title(
        self,
        request: Request[User, dict, Any],  # type: ignore
        data: AddUserTitleRequest,
        db_session: AsyncSession,
    ) -> UserTitleRead:
        user_id = request.user.id

        # 1. Find or Create Title
        stmt = select(Title).where(Title.external_id == data.external_id)
        result = await db_session.execute(stmt)
        title = result.scalar_one_or_none()

        if not title:
            # Map type string to Enum
            category_map = {
                "game": TitleCategory.GAME,
                "movie": TitleCategory.MOVIE,
                "tv": TitleCategory.SERIES,
                "anime": TitleCategory.ANIME
            }
            category = category_map.get(data.type, TitleCategory.GAME)

            # Create new title
            title = Title(
                name=data.name,
                category=category,
                external_id=str(data.external_id),
                cover_image=data.cover_url,
                release_year=data.release_year,
                description=None,
                genres=data.genres
            )
            db_session.add(title)
            await db_session.flush()

        # 2. Check if UserTitle exists
        stmt = select(UserTitle).where(
            UserTitle.user_id == user_id,
            UserTitle.title_id == title.id
        )
        result = await db_session.execute(stmt)
        user_title = result.scalar_one_or_none()

        is_new = user_title is None

        if user_title:
            # Update existing
            user_title.status = data.status
            user_title.score = data.score
            user_title.review_text = data.review_text
            user_title.is_spoiler = data.is_spoiler

            if data.finished_at:
                user_title.finished_at = data.finished_at.replace(tzinfo=None)
            elif data.status == UserTitleStatus.COMPLETED and not user_title.finished_at:
                user_title.finished_at = datetime.now()
            elif data.status != UserTitleStatus.COMPLETED:
                user_title.finished_at = None
        else:
            # Create new link
            finished_at = data.finished_at
            if finished_at:
                finished_at = finished_at.replace(tzinfo=None)

            if not finished_at and data.status == UserTitleStatus.COMPLETED:
                finished_at = datetime.now()

            user_title = UserTitle(
                user_id=user_id,
                title_id=title.id,
                status=data.status,
                score=data.score,
                review_text=data.review_text,
                is_spoiler=data.is_spoiler,
                finished_at=finished_at
            )
            db_session.add(user_title)

        await db_session.flush()

        # 3. Create notifications for followers (only for new titles)
        if is_new:
            follower_stmt = select(subscriptions_table.c.follower_id).where(
                subscriptions_table.c.following_id == user_id
            )
            follower_result = await db_session.execute(follower_stmt)
            follower_ids = [row[0] for row in follower_result.fetchall()]

            if follower_ids:
                notifications = [
                    Notification(
                        recipient_id=follower_id,
                        actor_id=user_id,
                        user_title_id=user_title.id,
                        type=NotificationType.NEW_TITLE,
                    )
                    for follower_id in follower_ids
                ]
                db_session.add_all(notifications)

        await db_session.commit()

        return UserTitleRead(
            id=user_title.id,
            user_id=user_title.user_id,
            title_id=user_title.title_id,
            status=user_title.status,
            score=user_title.score,
            is_spoiler=user_title.is_spoiler,
            finished_at=user_title.finished_at
        )
