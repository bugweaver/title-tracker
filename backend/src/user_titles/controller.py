from typing import Any
from datetime import datetime

from litestar import Controller, post, delete, get, put, patch, Request
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import (
    User,
    Title,
    UserTitle,
    TitleCategory,
    UserTitleStatus,
    TitleSeason,
    TitleEpisode,
    UserTitleSeason,
    UserTitleEpisode,
)
from core.models.notification import Notification, NotificationType
from core.models.user import subscriptions_table
from core.models.db_helper import get_db_session
from screenshots.schemas import ScreenshotRead
from .schemas import (
    AddUserTitleRequest,
    UpdateUserTitleStatusRequest,
    UserTitleStatusUpdateRead,
    UserTitleRead,
    UpdateSeasonRequest,
    UpdateEpisodeRequest,
    UpdateDlcRequest,
    SeriesStructureRead,
    SeasonStructureRead,
    GameDlcsRead,
)
from .score_cascade import (
    cascade_after_episode_change,
    cascade_after_season_change,
    reset_series_score_to_avg,
    reset_season_score_to_avg,
)
from .structure_sync import (
    supports_structure,
    sync_seasons_from_tmdb,
    sync_season_episodes_from_tmdb,
    sync_full_structure,
)
from .structure_read import build_structure_response
from .dlc_sync import sync_dlcs_from_igdb
from .dlc_read import build_game_dlcs_response


def _spoiler_from_text(text: str | None) -> bool:
    if not text:
        return False
    return "<" in text and ">" in text


async def _get_owned_user_title(
    db_session: AsyncSession,
    user_title_id: int,
    user_id: int,
) -> UserTitle:
    stmt = (
        select(UserTitle)
        .options(selectinload(UserTitle.title))
        .where(UserTitle.id == user_title_id)
    )
    result = await db_session.execute(stmt)
    user_title = result.scalar_one_or_none()
    if not user_title or user_title.user_id != user_id:
        raise NotFoundException(detail="Title not found")
    return user_title


async def _get_or_create_user_season(
    db_session: AsyncSession,
    user_title: UserTitle,
    season_number: int,
) -> tuple[UserTitleSeason, TitleSeason]:
    catalog_stmt = select(TitleSeason).where(
        TitleSeason.title_id == user_title.title_id,
        TitleSeason.season_number == season_number,
    )
    catalog_result = await db_session.execute(catalog_stmt)
    title_season = catalog_result.scalar_one_or_none()

    if not title_season:
        await sync_seasons_from_tmdb(db_session, user_title.title)
        catalog_result = await db_session.execute(catalog_stmt)
        title_season = catalog_result.scalar_one_or_none()

    if not title_season:
        raise NotFoundException(detail="Season not found")

    user_stmt = select(UserTitleSeason).where(
        UserTitleSeason.user_title_id == user_title.id,
        UserTitleSeason.title_season_id == title_season.id,
    )
    user_result = await db_session.execute(user_stmt)
    user_season = user_result.scalar_one_or_none()

    if not user_season:
        user_season = UserTitleSeason(
            user_title_id=user_title.id,
            title_season_id=title_season.id,
            status=UserTitleStatus.PLANNED,
        )
        db_session.add(user_season)
        await db_session.flush()

    return user_season, title_season


async def _get_or_create_user_episode(
    db_session: AsyncSession,
    user_title: UserTitle,
    user_season: UserTitleSeason,
    title_season: TitleSeason,
    episode_number: int,
) -> UserTitleEpisode:
    ep_stmt = select(TitleEpisode).where(
        TitleEpisode.title_season_id == title_season.id,
        TitleEpisode.episode_number == episode_number,
    )
    ep_result = await db_session.execute(ep_stmt)
    title_episode = ep_result.scalar_one_or_none()

    if not title_episode:
        await sync_season_episodes_from_tmdb(
            db_session, user_title.title, title_season
        )
        ep_result = await db_session.execute(ep_stmt)
        title_episode = ep_result.scalar_one_or_none()

    if not title_episode:
        raise NotFoundException(detail="Episode not found")

    user_ep_stmt = select(UserTitleEpisode).where(
        UserTitleEpisode.user_title_season_id == user_season.id,
        UserTitleEpisode.title_episode_id == title_episode.id,
    )
    user_ep_result = await db_session.execute(user_ep_stmt)
    user_episode = user_ep_result.scalar_one_or_none()

    if not user_episode:
        user_episode = UserTitleEpisode(
            user_title_season_id=user_season.id,
            title_episode_id=title_episode.id,
            status=UserTitleStatus.PLANNED,
        )
        db_session.add(user_episode)
        await db_session.flush()

    return user_episode


def _to_user_title_read(user_title: UserTitle) -> UserTitleRead:
    return UserTitleRead(
        id=user_title.id,
        user_id=user_title.user_id,
        title_id=user_title.title_id,
        status=user_title.status,
        score=user_title.score,
        avg_score=user_title.avg_score,
        score_is_manual=user_title.score_is_manual,
        is_spoiler=user_title.is_spoiler,
        finished_at=user_title.finished_at,
        times_completed=user_title.times_completed,
        is_completed_100_percent=user_title.is_completed_100_percent,
        game_platform=user_title.game_platform,
        progress_value=user_title.progress_value,
        screenshots=[
            ScreenshotRead.model_validate(s) for s in user_title.screenshots
        ],
    )


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

        category_map = {
            "game": TitleCategory.GAME,
            "movie": TitleCategory.MOVIE,
            "tv": TitleCategory.SERIES,
            "series": TitleCategory.SERIES,
            "anime": TitleCategory.ANIME,
            "manga": TitleCategory.MANGA,
            "comics": TitleCategory.COMICS,
            "book": TitleCategory.BOOK,
        }
        category = category_map.get(data.type, TitleCategory.GAME)

        stmt = select(Title).where(
            Title.external_id == data.external_id,
            Title.category == category,
        )
        result = await db_session.execute(stmt)
        title = result.scalar_one_or_none()

        if not title:
            title = Title(
                name=data.name,
                category=category,
                external_id=str(data.external_id),
                cover_image=data.cover_url,
                release_year=data.release_year,
                description=None,
                genres=data.genres,
            )
            db_session.add(title)
            await db_session.flush()

        stmt = select(UserTitle).where(
            UserTitle.user_id == user_id,
            UserTitle.title_id == title.id,
        )
        result = await db_session.execute(stmt)
        user_title = result.scalar_one_or_none()

        is_new = user_title is None
        has_meaningful_change = False
        is_completed_100_percent = (
            data.type == "game"
            and data.status == UserTitleStatus.COMPLETED
            and data.is_completed_100_percent
        )
        game_platform = data.game_platform if data.type == "game" else None
        progress_categories = {"game", "manga", "comics", "book"}
        progress_value = data.progress_value if data.type in progress_categories else None

        # Explicit score from client marks series score as manual unless told otherwise
        score_is_manual = data.score_is_manual
        if score_is_manual is None and data.score is not None:
            score_is_manual = True
        if score_is_manual is None:
            score_is_manual = False

        if user_title:
            previous_status = user_title.status
            should_increment = (
                data.status == UserTitleStatus.COMPLETED and data.increment_completion
            )

            if (
                user_title.status != data.status
                or user_title.score != data.score
                or user_title.review_text != data.review_text
                or user_title.is_completed_100_percent != is_completed_100_percent
                or user_title.game_platform != game_platform
                or user_title.progress_value != progress_value
                or should_increment
            ):
                has_meaningful_change = True

            user_title.status = data.status
            user_title.score = data.score
            user_title.score_is_manual = bool(score_is_manual) if data.score is not None else False
            if data.score is None:
                user_title.score_is_manual = False
            user_title.review_text = data.review_text
            user_title.is_spoiler = data.is_spoiler
            user_title.is_completed_100_percent = is_completed_100_percent
            user_title.game_platform = game_platform
            user_title.progress_value = progress_value

            if should_increment:
                user_title.times_completed += 1
            elif (
                data.status == UserTitleStatus.COMPLETED
                and previous_status != UserTitleStatus.COMPLETED
                and user_title.times_completed == 0
            ):
                user_title.times_completed = 1

            if data.finished_at:
                user_title.finished_at = data.finished_at.replace(tzinfo=None)
            elif data.status == UserTitleStatus.COMPLETED and not user_title.finished_at:
                user_title.finished_at = datetime.now()
            elif data.status != UserTitleStatus.COMPLETED:
                user_title.finished_at = None
        else:
            finished_at = data.finished_at
            if finished_at:
                finished_at = finished_at.replace(tzinfo=None)

            if not finished_at and data.status == UserTitleStatus.COMPLETED:
                finished_at = datetime.now()

            times_completed = 1 if data.status == UserTitleStatus.COMPLETED else 0

            user_title = UserTitle(
                user_id=user_id,
                title_id=title.id,
                status=data.status,
                score=data.score,
                score_is_manual=bool(score_is_manual) if data.score is not None else False,
                review_text=data.review_text,
                is_spoiler=data.is_spoiler,
                finished_at=finished_at,
                times_completed=times_completed,
                is_completed_100_percent=is_completed_100_percent,
                game_platform=game_platform,
                progress_value=progress_value,
            )
            db_session.add(user_title)

        await db_session.flush()

        if supports_structure(category):
            await sync_full_structure(db_session, user_title, load_all_episodes=False)
        elif category == TitleCategory.GAME and not title.parent_title_id:
            await sync_dlcs_from_igdb(db_session, title)

        should_notify = is_new or has_meaningful_change
        if should_notify:
            notif_type = (
                NotificationType.NEW_TITLE if is_new else NotificationType.TITLE_UPDATED
            )

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
                        type=notif_type,
                    )
                    for follower_id in follower_ids
                ]
                db_session.add_all(notifications)

        await db_session.commit()
        await db_session.refresh(user_title)

        return _to_user_title_read(user_title)

    @patch("/{user_title_id:int}/status")
    async def update_user_title_status(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        data: UpdateUserTitleStatusRequest,
        db_session: AsyncSession,
    ) -> UserTitleStatusUpdateRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        previous_status = user_title.status

        if previous_status == data.status:
            return UserTitleStatusUpdateRead(
                id=user_title.id,
                status=user_title.status,
                finished_at=user_title.finished_at,
                times_completed=user_title.times_completed,
                updated_at=user_title.updated_at,
            )

        user_title.status = data.status

        if data.status == UserTitleStatus.COMPLETED:
            if not user_title.finished_at:
                user_title.finished_at = datetime.now()
            if (
                previous_status != UserTitleStatus.COMPLETED
                and user_title.times_completed == 0
            ):
                user_title.times_completed = 1
        else:
            user_title.finished_at = None

        follower_stmt = select(subscriptions_table.c.follower_id).where(
            subscriptions_table.c.following_id == request.user.id
        )
        follower_result = await db_session.execute(follower_stmt)
        follower_ids = [row[0] for row in follower_result.fetchall()]

        if follower_ids:
            db_session.add_all(
                [
                    Notification(
                        recipient_id=follower_id,
                        actor_id=request.user.id,
                        user_title_id=user_title.id,
                        type=NotificationType.TITLE_UPDATED,
                    )
                    for follower_id in follower_ids
                ]
            )

        await db_session.commit()
        await db_session.refresh(user_title)

        return UserTitleStatusUpdateRead(
            id=user_title.id,
            status=user_title.status,
            finished_at=user_title.finished_at,
            times_completed=user_title.times_completed,
            updated_at=user_title.updated_at,
        )

    @delete("/{user_title_id:int}", status_code=204)
    async def delete_user_title(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        db_session: AsyncSession,
    ) -> None:
        """Delete a title from the current user's list."""
        stmt = select(UserTitle).where(UserTitle.id == user_title_id)
        result = await db_session.execute(stmt)
        user_title = result.scalar_one_or_none()

        if not user_title or user_title.user_id != request.user.id:
            raise NotFoundException(detail="Title not found")

        await db_session.delete(user_title)
        await db_session.commit()

    async def _read_structure(
        self,
        db_session: AsyncSession,
        user_title: UserTitle,
        *,
        sync_seasons: bool = False,
    ) -> SeriesStructureRead:
        if sync_seasons:
            await sync_seasons_from_tmdb(db_session, user_title.title)
            await db_session.flush()

        seasons_stmt = (
            select(TitleSeason)
            .options(selectinload(TitleSeason.episodes))
            .where(TitleSeason.title_id == user_title.title_id)
            .order_by(TitleSeason.season_number)
            .execution_options(populate_existing=True)
        )
        seasons_result = await db_session.execute(seasons_stmt)
        catalog_seasons = list(seasons_result.scalars().unique().all())

        if not catalog_seasons and not sync_seasons:
            await sync_seasons_from_tmdb(db_session, user_title.title)
            await db_session.flush()
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

        # Refresh only scalars. A full refresh re-selectins UserTitle.seasons and
        # expires already-loaded UserTitleSeason.episodes → MissingGreenlet in async.
        await db_session.refresh(
            user_title,
            attribute_names=[
                "score",
                "avg_score",
                "score_is_manual",
                "status",
                "review_text",
                "is_spoiler",
            ],
        )
        return build_structure_response(
            user_title, catalog_seasons, user_seasons_by_catalog_id
        )

    @get("/{user_title_id:int}/dlcs")
    async def get_dlcs(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        db_session: AsyncSession,
    ) -> GameDlcsRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if user_title.title.category != TitleCategory.GAME:
            raise HTTPException(detail="Not a game", status_code=400)
        if user_title.title.parent_title_id is not None:
            raise HTTPException(detail="DLC has no nested DLC list", status_code=400)

        response = await build_game_dlcs_response(db_session, user_title, sync=True)
        await db_session.commit()
        return response

    @post("/{user_title_id:int}/sync-dlcs")
    async def sync_dlcs(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        db_session: AsyncSession,
    ) -> GameDlcsRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if user_title.title.category != TitleCategory.GAME:
            raise HTTPException(detail="Not a game", status_code=400)
        if user_title.title.parent_title_id is not None:
            raise HTTPException(detail="DLC has no nested DLC list", status_code=400)

        response = await build_game_dlcs_response(db_session, user_title, sync=True)
        await db_session.commit()
        return response

    @put("/{user_title_id:int}/dlcs/{dlc_title_id:int}")
    async def update_dlc(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        dlc_title_id: int,
        data: UpdateDlcRequest,
        db_session: AsyncSession,
    ) -> GameDlcsRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if user_title.title.category != TitleCategory.GAME:
            raise HTTPException(detail="Not a game", status_code=400)

        dlc_title = await db_session.get(Title, dlc_title_id)
        if (
            not dlc_title
            or dlc_title.category != TitleCategory.GAME
            or dlc_title.parent_title_id != user_title.title_id
        ):
            raise NotFoundException(detail="DLC not found for this game")

        dlc_user_stmt = select(UserTitle).where(
            UserTitle.user_id == request.user.id,
            UserTitle.title_id == dlc_title.id,
        )
        dlc_user_result = await db_session.execute(dlc_user_stmt)
        dlc_user_title = dlc_user_result.scalar_one_or_none()

        if not dlc_user_title:
            status = data.status or UserTitleStatus.PLANNED
            finished_at = datetime.now() if status == UserTitleStatus.COMPLETED else None
            dlc_user_title = UserTitle(
                user_id=request.user.id,
                title_id=dlc_title.id,
                status=status,
                score=None if data.clear_score else data.score,
                score_is_manual=bool(data.score) and not data.clear_score,
                review_text=data.review_text,
                is_spoiler=(
                    data.is_spoiler
                    if data.is_spoiler is not None
                    else _spoiler_from_text(data.review_text)
                ),
                finished_at=finished_at,
                times_completed=1 if status == UserTitleStatus.COMPLETED else 0,
            )
            db_session.add(dlc_user_title)
        else:
            if data.status is not None:
                previous_status = dlc_user_title.status
                dlc_user_title.status = data.status
                if data.status == UserTitleStatus.COMPLETED:
                    if not dlc_user_title.finished_at:
                        dlc_user_title.finished_at = datetime.now()
                    if (
                        previous_status != UserTitleStatus.COMPLETED
                        and dlc_user_title.times_completed == 0
                    ):
                        dlc_user_title.times_completed = 1
                else:
                    dlc_user_title.finished_at = None

            if data.clear_score:
                dlc_user_title.score = None
                dlc_user_title.score_is_manual = False
            elif data.score is not None:
                dlc_user_title.score = data.score
                dlc_user_title.score_is_manual = True

            if data.review_text is not None:
                dlc_user_title.review_text = data.review_text
                dlc_user_title.is_spoiler = (
                    data.is_spoiler
                    if data.is_spoiler is not None
                    else _spoiler_from_text(data.review_text)
                )
            elif data.is_spoiler is not None:
                dlc_user_title.is_spoiler = data.is_spoiler

        await db_session.flush()
        response = await build_game_dlcs_response(db_session, user_title, sync=False)
        await db_session.commit()
        return response

    @delete("/{user_title_id:int}/dlcs/{dlc_title_id:int}", status_code=204)
    async def delete_dlc_tracking(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        dlc_title_id: int,
        db_session: AsyncSession,
    ) -> None:
        """Remove user tracking for a DLC (catalog title stays linked to the game)."""
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if user_title.title.category != TitleCategory.GAME:
            raise HTTPException(detail="Not a game", status_code=400)

        dlc_title = await db_session.get(Title, dlc_title_id)
        if (
            not dlc_title
            or dlc_title.parent_title_id != user_title.title_id
        ):
            raise NotFoundException(detail="DLC not found for this game")

        dlc_user_stmt = select(UserTitle).where(
            UserTitle.user_id == request.user.id,
            UserTitle.title_id == dlc_title.id,
        )
        dlc_user_result = await db_session.execute(dlc_user_stmt)
        dlc_user_title = dlc_user_result.scalar_one_or_none()
        if not dlc_user_title:
            raise NotFoundException(detail="DLC tracking not found")

        await db_session.delete(dlc_user_title)
        await db_session.commit()

    @get("/{user_title_id:int}/structure")
    async def get_structure(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        db_session: AsyncSession,
    ) -> SeriesStructureRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if not supports_structure(user_title.title.category):
            raise HTTPException(detail="Not a series or anime", status_code=400)

        structure = await self._read_structure(db_session, user_title)
        await db_session.commit()
        return structure

    @post("/{user_title_id:int}/sync-structure")
    async def sync_structure(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        db_session: AsyncSession,
    ) -> SeriesStructureRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if not supports_structure(user_title.title.category):
            raise HTTPException(detail="Not a series or anime", status_code=400)

        await sync_full_structure(db_session, user_title, load_all_episodes=False)
        structure = await self._read_structure(
            db_session, user_title, sync_seasons=False
        )
        await db_session.commit()
        return structure

    @post("/{user_title_id:int}/seasons/{season_number:int}/sync-episodes")
    async def sync_season_episodes(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        season_number: int,
        db_session: AsyncSession,
    ) -> SeasonStructureRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if not supports_structure(user_title.title.category):
            raise HTTPException(detail="Not a series or anime", status_code=400)

        _user_season, title_season = await _get_or_create_user_season(
            db_session, user_title, season_number
        )
        await sync_season_episodes_from_tmdb(
            db_session, user_title.title, title_season
        )
        structure = await self._read_structure(db_session, user_title)
        await db_session.commit()
        for season in structure.seasons:
            if season.season_number == season_number:
                return season
        raise NotFoundException(detail="Season not found")

    @put("/{user_title_id:int}/seasons/{season_number:int}")
    async def update_season(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        season_number: int,
        data: UpdateSeasonRequest,
        db_session: AsyncSession,
    ) -> SeriesStructureRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if not supports_structure(user_title.title.category):
            raise HTTPException(detail="Not a series or anime", status_code=400)

        user_season, _title_season = await _get_or_create_user_season(
            db_session, user_title, season_number
        )

        if data.status is not None:
            user_season.status = data.status

        if data.clear_score:
            user_season.score = None
            user_season.score_is_manual = False
        elif data.score is not None:
            user_season.score = data.score
            user_season.score_is_manual = True

        if data.review_text is not None:
            user_season.review_text = data.review_text
            user_season.is_spoiler = (
                data.is_spoiler
                if data.is_spoiler is not None
                else _spoiler_from_text(data.review_text)
            )
        elif data.is_spoiler is not None:
            user_season.is_spoiler = data.is_spoiler

        await db_session.flush()
        await cascade_after_season_change(db_session, user_season)
        structure = await self._read_structure(db_session, user_title)
        await db_session.commit()
        return structure

    @put("/{user_title_id:int}/seasons/{season_number:int}/episodes/{episode_number:int}")
    async def update_episode(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        season_number: int,
        episode_number: int,
        data: UpdateEpisodeRequest,
        db_session: AsyncSession,
    ) -> SeriesStructureRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if not supports_structure(user_title.title.category):
            raise HTTPException(detail="Not a series or anime", status_code=400)

        user_season, title_season = await _get_or_create_user_season(
            db_session, user_title, season_number
        )
        user_episode = await _get_or_create_user_episode(
            db_session, user_title, user_season, title_season, episode_number
        )

        if data.status is not None:
            user_episode.status = data.status

        if data.clear_score:
            user_episode.score = None
        elif data.score is not None:
            user_episode.score = data.score

        await db_session.flush()
        await cascade_after_episode_change(db_session, user_season)
        structure = await self._read_structure(db_session, user_title)
        await db_session.commit()
        return structure

    @post("/{user_title_id:int}/reset-score")
    async def reset_series_score(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        db_session: AsyncSession,
    ) -> SeriesStructureRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        await reset_series_score_to_avg(db_session, user_title)

        if supports_structure(user_title.title.category):
            structure = await self._read_structure(db_session, user_title)
            await db_session.commit()
            return structure

        await db_session.commit()
        return SeriesStructureRead(
            user_title_id=user_title.id,
            title_id=user_title.title_id,
            score=user_title.score,
            avg_score=user_title.avg_score,
            score_is_manual=user_title.score_is_manual,
            status=user_title.status,
            review_text=user_title.review_text,
            seasons=[],
        )

    @post("/{user_title_id:int}/seasons/{season_number:int}/reset-score")
    async def reset_season_score(
        self,
        request: Request[User, dict, Any],  # type: ignore
        user_title_id: int,
        season_number: int,
        db_session: AsyncSession,
    ) -> SeriesStructureRead:
        user_title = await _get_owned_user_title(
            db_session, user_title_id, request.user.id
        )
        if not supports_structure(user_title.title.category):
            raise HTTPException(detail="Not a series or anime", status_code=400)

        user_season, _title_season = await _get_or_create_user_season(
            db_session, user_title, season_number
        )
        await reset_season_score_to_avg(db_session, user_season)
        structure = await self._read_structure(db_session, user_title)
        await db_session.commit()
        return structure
