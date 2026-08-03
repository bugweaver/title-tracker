from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from litestar import Controller, get, post, Request
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.security.jwt import Token

from core.models.db_helper import get_db_session
from core.models import User, Title, UserTitle, ReviewView
from users.schemas import UserRead
from .schemas import (
    TitleCreate,
    TitleRead,
    UserTitleRead,
    UserTitleCreate,
    ReviewViewRecordResponse,
    ReviewViewsResponse,
)


async def provide_titles_service(db_session: AsyncSession):
    # Ideally should be a separate service, but keeping it simple for now as per plan
    return db_session


class TitleController(Controller):
    path = "/titles"
    tags = ["Titles"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/my")
    async def get_my_titles(
        self, request: Request[User, Token, Any], db_session: AsyncSession
    ) -> list[UserTitleRead]:
        """Get all titles for the current user."""
        return await self._get_titles_for_user(
            request.user.id, db_session, include_view_counts=True
        )

    @get("/user/{user_id:int}")
    async def get_user_titles(
        self, user_id: int, db_session: AsyncSession
    ) -> list[UserTitleRead]:
        """Get public titles for a specific user."""
        return await self._get_titles_for_user(user_id, db_session)

    async def _get_titles_for_user(
        self,
        user_id: int,
        db_session: AsyncSession,
        include_view_counts: bool = False,
    ) -> list[UserTitleRead]:
        stmt = (
            select(UserTitle)
            .options(selectinload(UserTitle.title))
            .where(UserTitle.user_id == user_id)
            .order_by(UserTitle.updated_at.desc())
        )

        result = await db_session.execute(stmt)
        user_titles = result.scalars().all()

        view_counts: dict[int, int] = {}
        if include_view_counts and user_titles:
            counts_stmt = (
                select(ReviewView.user_title_id, func.count())
                .where(ReviewView.user_title_id.in_([ut.id for ut in user_titles]))
                .group_by(ReviewView.user_title_id)
            )
            counts_result = await db_session.execute(counts_stmt)
            view_counts = {row[0]: row[1] for row in counts_result.all()}

        items: list[UserTitleRead] = []
        for ut in user_titles:
            item = UserTitleRead.model_validate(ut)
            if include_view_counts:
                item.view_count = view_counts.get(ut.id, 0)
            items.append(item)
        return items

    @get("/entry/{user_title_id:int}")
    async def get_user_title_entry(
        self,
        user_title_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> UserTitleRead:
        """Get a single user-title entry by its ID (for review page)."""
        stmt = (
            select(UserTitle)
            .options(selectinload(UserTitle.title))
            .where(UserTitle.id == user_title_id)
        )
        result = await db_session.execute(stmt)
        user_title = result.scalar_one_or_none()

        if not user_title:
            raise NotFoundException(detail="Entry not found")

        item = UserTitleRead.model_validate(user_title)
        if request.user.id == user_title.user_id:
            count_stmt = select(func.count()).select_from(ReviewView).where(
                ReviewView.user_title_id == user_title_id
            )
            count_result = await db_session.execute(count_stmt)
            item.view_count = count_result.scalar() or 0

        return item

    @post("/entry/{user_title_id:int}/view")
    async def record_review_view(
        self,
        user_title_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> ReviewViewRecordResponse:
        """Record that the current user viewed a review. Owners are not counted."""
        user_title = await db_session.get(UserTitle, user_title_id)
        if not user_title:
            raise NotFoundException(detail="Entry not found")

        if request.user.id == user_title.user_id:
            return ReviewViewRecordResponse(recorded=False)

        existing_stmt = select(ReviewView).where(
            ReviewView.user_title_id == user_title_id,
            ReviewView.viewer_id == request.user.id,
        )
        existing_result = await db_session.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Touch viewed_at so repeat visits bubble up in the viewers list
            existing.viewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db_session.commit()
            return ReviewViewRecordResponse(recorded=False)

        db_session.add(
            ReviewView(
                user_title_id=user_title_id,
                viewer_id=request.user.id,
            )
        )
        await db_session.commit()
        return ReviewViewRecordResponse(recorded=True)

    @get("/entry/{user_title_id:int}/viewers")
    async def get_review_viewers(
        self,
        user_title_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> ReviewViewsResponse:
        """List users who viewed this review. Owner only."""
        user_title = await db_session.get(UserTitle, user_title_id)
        if not user_title:
            raise NotFoundException(detail="Entry not found")

        if request.user.id != user_title.user_id:
            raise HTTPException(detail="Forbidden", status_code=403)

        count_stmt = select(func.count()).select_from(ReviewView).where(
            ReviewView.user_title_id == user_title_id
        )
        count_result = await db_session.execute(count_stmt)
        count = count_result.scalar() or 0

        viewers_stmt = (
            select(User)
            .join(ReviewView, ReviewView.viewer_id == User.id)
            .where(ReviewView.user_title_id == user_title_id)
            .order_by(ReviewView.viewed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        viewers_result = await db_session.execute(viewers_stmt)
        viewers = viewers_result.scalars().all()

        return ReviewViewsResponse(
            count=count,
            viewers=[UserRead.model_validate(u) for u in viewers],
        )

    @post("/")
    async def create_title(
        self, data: TitleCreate, db_session: AsyncSession
    ) -> TitleRead:
        """Create a new title (admin/system function usually, but open for now for testing)."""
        title = Title(**data.model_dump())
        db_session.add(title)
        await db_session.commit()
        await db_session.refresh(title)

        return TitleRead.model_validate(title)

    @post("/add_to_user")
    async def add_title_to_user(
        self,
        request: Request[User, Token, Any],
        data: UserTitleCreate,
        db_session: AsyncSession,
    ) -> UserTitleRead:
        """Add a title to the current user's list."""
        user_id = request.user.id

        user_title = UserTitle(
            user_id=user_id,
            title_id=data.title_id,
            status=data.status,
            score=data.score,
        )

        db_session.add(user_title)
        await db_session.commit()

        # Reload to get title relationship
        stmt = (
            select(UserTitle)
            .options(selectinload(UserTitle.title))
            .where(UserTitle.id == user_title.id)
        )
        result = await db_session.execute(stmt)
        created_user_title = result.scalar_one()

        return UserTitleRead.model_validate(created_user_title)
