from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from litestar import Controller, delete, get, post, put, Request
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.security.jwt import Token

from core.models.db_helper import get_db_session
from core.models import (
    User,
    Title,
    UserTitle,
    ReviewView,
    ReviewComment,
    ReviewReaction,
    Notification,
    NotificationType,
    UserTitleStatus,
    TitleCategory,
    TitleSeason,
    UserTitleSeason,
    UserTitleEpisode,
)
from core.privacy import ensure_can_view_user_library
from users.schemas import UserRead
from user_titles.schemas import SeriesStructureRead, SeasonStructureRead, GameDlcsRead
from user_titles.structure_read import build_structure_response
from user_titles.structure_sync import (
    supports_structure,
    sync_season_episodes_from_tmdb,
)
from user_titles.dlc_read import build_game_dlcs_response
from .schemas import (
    TitleCreate,
    TitleRead,
    UserTitleRead,
    UserTitleCreate,
    ReviewViewRecordResponse,
    ReviewViewsResponse,
    ReviewCommentCreate,
    ReviewCommentRead,
    ReviewReactionSet,
    ReviewReactionsResponse,
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
        self,
        user_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> list[UserTitleRead]:
        """Get public titles for a specific user."""
        await self._ensure_can_view_user_library(
            owner_id=user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )
        return await self._get_titles_for_user(user_id, db_session)

    async def _ensure_can_view_user_library(
        self,
        owner_id: int,
        viewer_id: int,
        db_session: AsyncSession,
    ) -> None:
        await ensure_can_view_user_library(owner_id, viewer_id, db_session)

    async def _get_user_title_or_404(
        self, user_title_id: int, db_session: AsyncSession
    ) -> UserTitle:
        user_title = await db_session.get(UserTitle, user_title_id)
        if not user_title:
            raise NotFoundException(detail="Entry not found")
        return user_title

    async def _get_titles_for_user(
        self,
        user_id: int,
        db_session: AsyncSession,
        include_view_counts: bool = False,
    ) -> list[UserTitleRead]:
        stmt = (
            select(UserTitle)
            .join(Title, UserTitle.title_id == Title.id)
            .options(selectinload(UserTitle.title))
            .where(
                UserTitle.user_id == user_id,
                # DLC/expansions are managed under the parent game
                Title.parent_title_id.is_(None),
            )
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

        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )

        item = UserTitleRead.model_validate(user_title)
        if request.user.id == user_title.user_id:
            count_stmt = select(func.count()).select_from(ReviewView).where(
                ReviewView.user_title_id == user_title_id
            )
            count_result = await db_session.execute(count_stmt)
            item.view_count = count_result.scalar() or 0

        return item

    @get("/entry/{user_title_id:int}/dlcs")
    async def get_user_title_dlcs(
        self,
        user_title_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> GameDlcsRead:
        """Public DLC list for a game user-title entry."""
        stmt = (
            select(UserTitle)
            .options(selectinload(UserTitle.title))
            .where(UserTitle.id == user_title_id)
        )
        result = await db_session.execute(stmt)
        user_title = result.scalar_one_or_none()
        if not user_title:
            raise NotFoundException(detail="Entry not found")
        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )
        if user_title.title.category != TitleCategory.GAME:
            raise HTTPException(detail="Not a game", status_code=400)
        if user_title.title.parent_title_id is not None:
            raise HTTPException(detail="DLC has no nested DLC list", status_code=400)

        # Public view uses catalog already linked; avoid IGDB calls on every view
        return await build_game_dlcs_response(db_session, user_title, sync=False)

    @get("/entry/{user_title_id:int}/structure")
    async def get_user_title_structure(
        self,
        user_title_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> SeriesStructureRead:
        """Public series structure (seasons/episodes) for a user-title entry."""
        stmt = (
            select(UserTitle)
            .options(selectinload(UserTitle.title))
            .where(UserTitle.id == user_title_id)
        )
        result = await db_session.execute(stmt)
        user_title = result.scalar_one_or_none()
        if not user_title:
            raise NotFoundException(detail="Entry not found")
        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )
        if not supports_structure(user_title.title.category):
            raise HTTPException(detail="Not a series or anime", status_code=400)

        seasons_stmt = (
            select(TitleSeason)
            .options(selectinload(TitleSeason.episodes))
            .where(TitleSeason.title_id == user_title.title_id)
            .order_by(TitleSeason.season_number)
            .execution_options(populate_existing=True)
        )
        seasons_result = await db_session.execute(seasons_stmt)
        catalog_seasons = list(seasons_result.scalars().unique().all())

        user_seasons_stmt = (
            select(UserTitleSeason)
            .options(
                selectinload(UserTitleSeason.episodes).selectinload(
                    UserTitleEpisode.title_episode
                )
            )
            .where(UserTitleSeason.user_title_id == user_title.id)
        )
        user_seasons_result = await db_session.execute(user_seasons_stmt)
        user_seasons = list(user_seasons_result.scalars().unique().all())
        user_seasons_by_catalog_id = {us.title_season_id: us for us in user_seasons}

        return build_structure_response(
            user_title, catalog_seasons, user_seasons_by_catalog_id
        )

    @post("/entry/{user_title_id:int}/seasons/{season_number:int}/sync-episodes")
    async def sync_public_season_episodes(
        self,
        user_title_id: int,
        season_number: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> SeasonStructureRead:
        """Sync episode catalog for a season (any authenticated viewer)."""
        stmt = (
            select(UserTitle)
            .options(selectinload(UserTitle.title))
            .where(UserTitle.id == user_title_id)
        )
        result = await db_session.execute(stmt)
        user_title = result.scalar_one_or_none()
        if not user_title:
            raise NotFoundException(detail="Entry not found")
        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )
        if not supports_structure(user_title.title.category):
            raise HTTPException(detail="Not a series or anime", status_code=400)

        season_stmt = select(TitleSeason).where(
            TitleSeason.title_id == user_title.title_id,
            TitleSeason.season_number == season_number,
        )
        season_result = await db_session.execute(season_stmt)
        title_season = season_result.scalar_one_or_none()
        if not title_season:
            raise NotFoundException(detail="Season not found")

        await sync_season_episodes_from_tmdb(
            db_session, user_title.title, title_season
        )
        await db_session.commit()

        structure = await self.get_user_title_structure(
            user_title_id, request, db_session
        )
        for season in structure.seasons:
            if season.season_number == season_number:
                return season
        raise NotFoundException(detail="Season not found")

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

    @get("/entry/{user_title_id:int}/comments")
    async def list_review_comments(
        self,
        user_title_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReviewCommentRead]:
        user_title = await self._get_user_title_or_404(user_title_id, db_session)
        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )
        stmt = (
            select(ReviewComment)
            .options(selectinload(ReviewComment.author))
            .where(ReviewComment.user_title_id == user_title_id)
            .order_by(ReviewComment.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db_session.execute(stmt)
        return [ReviewCommentRead.model_validate(c) for c in result.scalars().all()]

    @post("/entry/{user_title_id:int}/comments")
    async def create_review_comment(
        self,
        user_title_id: int,
        data: ReviewCommentCreate,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> ReviewCommentRead:
        user_title = await self._get_user_title_or_404(user_title_id, db_session)
        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )
        body = data.body.strip()
        if not body:
            raise HTTPException(detail="Comment cannot be empty", status_code=400)

        comment = ReviewComment(
            user_title_id=user_title_id,
            author_id=request.user.id,
            body=body,
        )
        db_session.add(comment)

        if request.user.id != user_title.user_id:
            db_session.add(
                Notification(
                    recipient_id=user_title.user_id,
                    actor_id=request.user.id,
                    user_title_id=user_title_id,
                    type=NotificationType.NEW_COMMENT,
                )
            )

        await db_session.commit()
        await db_session.refresh(comment)
        stmt = (
            select(ReviewComment)
            .options(selectinload(ReviewComment.author))
            .where(ReviewComment.id == comment.id)
        )
        result = await db_session.execute(stmt)
        return ReviewCommentRead.model_validate(result.scalar_one())

    @delete("/entry/{user_title_id:int}/comments/{comment_id:int}", status_code=204)
    async def delete_review_comment(
        self,
        user_title_id: int,
        comment_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> None:
        user_title = await self._get_user_title_or_404(user_title_id, db_session)
        comment = await db_session.get(ReviewComment, comment_id)
        if not comment or comment.user_title_id != user_title_id:
            raise NotFoundException(detail="Comment not found")
        if (
            comment.author_id != request.user.id
            and user_title.user_id != request.user.id
        ):
            raise HTTPException(detail="Forbidden", status_code=403)
        await db_session.delete(comment)
        await db_session.commit()

    @get("/entry/{user_title_id:int}/reactions")
    async def get_review_reactions(
        self,
        user_title_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> ReviewReactionsResponse:
        user_title = await self._get_user_title_or_404(user_title_id, db_session)
        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )
        counts_stmt = (
            select(ReviewReaction.type, func.count())
            .where(ReviewReaction.user_title_id == user_title_id)
            .group_by(ReviewReaction.type)
        )
        counts_result = await db_session.execute(counts_stmt)
        counts: dict[str, int] = {}
        for row in counts_result.all():
            key = row[0].value if hasattr(row[0], "value") else str(row[0])
            counts[key] = row[1]

        my_stmt = select(ReviewReaction).where(
            ReviewReaction.user_title_id == user_title_id,
            ReviewReaction.user_id == request.user.id,
        )
        my_result = await db_session.execute(my_stmt)
        my_reaction = my_result.scalar_one_or_none()

        my_type = None
        if my_reaction is not None:
            raw = my_reaction.type
            my_type = raw.value if hasattr(raw, "value") else str(raw)

        return ReviewReactionsResponse(
            counts=counts,
            my_reaction=my_type,
            total=sum(counts.values()),
        )

    @put("/entry/{user_title_id:int}/reactions")
    async def set_review_reaction(
        self,
        user_title_id: int,
        data: ReviewReactionSet,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> ReviewReactionsResponse:
        user_title = await self._get_user_title_or_404(user_title_id, db_session)
        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )

        existing_stmt = select(ReviewReaction).where(
            ReviewReaction.user_title_id == user_title_id,
            ReviewReaction.user_id == request.user.id,
        )
        existing_result = await db_session.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        is_new = existing is None
        if existing:
            existing.type = data.type
        else:
            db_session.add(
                ReviewReaction(
                    user_title_id=user_title_id,
                    user_id=request.user.id,
                    type=data.type,
                )
            )

        if is_new and request.user.id != user_title.user_id:
            db_session.add(
                Notification(
                    recipient_id=user_title.user_id,
                    actor_id=request.user.id,
                    user_title_id=user_title_id,
                    type=NotificationType.NEW_REACTION,
                )
            )

        await db_session.commit()
        return await self.get_review_reactions(user_title_id, request, db_session)

    @delete("/entry/{user_title_id:int}/reactions", status_code=204)
    async def delete_review_reaction(
        self,
        user_title_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> None:
        user_title = await self._get_user_title_or_404(user_title_id, db_session)
        await self._ensure_can_view_user_library(
            owner_id=user_title.user_id,
            viewer_id=request.user.id,
            db_session=db_session,
        )
        existing_stmt = select(ReviewReaction).where(
            ReviewReaction.user_title_id == user_title_id,
            ReviewReaction.user_id == request.user.id,
        )
        existing_result = await db_session.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()
        if existing:
            await db_session.delete(existing)
            await db_session.commit()

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
            times_completed=1 if data.status == UserTitleStatus.COMPLETED else 0,
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
