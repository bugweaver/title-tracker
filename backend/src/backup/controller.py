import json
import logging
from datetime import datetime
from typing import Annotated, Any

from litestar import Controller, get, post, Request, Response
from litestar.di import Provide
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from core.models.title import Title, UserTitle, TitleCategory
from core.models.season import (
    TitleSeason,
    TitleEpisode,
    UserTitleSeason,
    UserTitleEpisode,
)
from core.models.db_helper import get_db_session
from core.models import User, TitleScreenshot
from core.s3 import MAX_SCREENSHOTS_PER_ENTRY, parse_s3_key_from_url

from .schemas import (
    BackupItem,
    BackupResponse,
    BackupSeasonItem,
    BackupEpisodeItem,
    BackupDlcItem,
)

logger = logging.getLogger(__name__)


class BackupController(Controller):
    path = "/backup"
    tags = ["Backup"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/export")
    async def export_backup(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> Response:
        """Export all user titles to a JSON file."""
        user = request.user
        stmt = (
            select(UserTitle)
            .join(Title, UserTitle.title_id == Title.id)
            .where(UserTitle.user_id == user.id)
            .options(
                selectinload(UserTitle.title),
                selectinload(UserTitle.screenshots),
                selectinload(UserTitle.seasons)
                .selectinload(UserTitleSeason.title_season)
                .selectinload(TitleSeason.episodes),
                selectinload(UserTitle.seasons)
                .selectinload(UserTitleSeason.episodes)
                .selectinload(UserTitleEpisode.title_episode),
            )
        )
        result = await db_session.execute(stmt)
        user_titles = list(result.scalars().unique().all())

        by_title_id = {ut.title_id: ut for ut in user_titles}
        parent_uts = [
            ut for ut in user_titles if ut.title.parent_title_id is None
        ]
        dlc_by_parent: dict[int, list[UserTitle]] = {}
        for ut in user_titles:
            parent_id = ut.title.parent_title_id
            if parent_id is not None:
                dlc_by_parent.setdefault(parent_id, []).append(ut)

        backup_data = []
        for user_title in parent_uts:
            title = user_title.title
            seasons_payload = self._export_seasons(user_title)
            dlcs_payload = [
                self._export_dlc(dlc_ut)
                for dlc_ut in sorted(
                    dlc_by_parent.get(title.id, []),
                    key=lambda x: x.title.name.lower(),
                )
            ]

            item = BackupItem(
                external_id=title.external_id,
                type=title.category,
                title=title.name,
                poster_url=title.cover_image,
                release_year=title.release_year,
                genres=title.genres or [],
                status=user_title.status,
                score=user_title.score,
                review_text=user_title.review_text,
                is_spoiler=user_title.is_spoiler,
                finished_at=user_title.finished_at,
                times_completed=user_title.times_completed,
                is_completed_100_percent=user_title.is_completed_100_percent,
                game_platform=user_title.game_platform,
                progress_value=user_title.progress_value,
                screenshots=[s.url for s in user_title.screenshots],
                seasons=seasons_payload or None,
                dlcs=dlcs_payload or None,
            )
            backup_data.append(item.model_dump(mode="json"))

        # Keep orphan DLC rows (parent not in library) as root items
        for ut in user_titles:
            parent_id = ut.title.parent_title_id
            if parent_id is None:
                continue
            if parent_id in by_title_id:
                continue
            item = BackupItem(
                external_id=ut.title.external_id,
                type=ut.title.category,
                title=ut.title.name,
                poster_url=ut.title.cover_image,
                release_year=ut.title.release_year,
                genres=ut.title.genres or [],
                status=ut.status,
                score=ut.score,
                review_text=ut.review_text,
                is_spoiler=ut.is_spoiler,
                finished_at=ut.finished_at,
                times_completed=ut.times_completed,
                is_completed_100_percent=ut.is_completed_100_percent,
                game_platform=ut.game_platform,
                progress_value=ut.progress_value,
                screenshots=[s.url for s in ut.screenshots],
            )
            backup_data.append(item.model_dump(mode="json"))

        json_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
        filename = f"backup_{datetime.now().strftime('%Y-%m-%d')}.txt"

        return Response(
            content=json_content.encode("utf-8"),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    def _export_seasons(self, user_title: UserTitle) -> list[BackupSeasonItem]:
        seasons: list[BackupSeasonItem] = []
        for user_season in sorted(
            user_title.seasons or [],
            key=lambda s: s.title_season.season_number if s.title_season else 0,
        ):
            catalog = user_season.title_season
            if not catalog:
                continue
            user_eps_by_number = {
                ue.title_episode.episode_number: ue
                for ue in (user_season.episodes or [])
                if ue.title_episode
            }
            episodes: list[BackupEpisodeItem] = []
            for catalog_ep in sorted(
                catalog.episodes or [], key=lambda e: e.episode_number
            ):
                user_ep = user_eps_by_number.get(catalog_ep.episode_number)
                if not user_ep:
                    continue
                episodes.append(
                    BackupEpisodeItem(
                        episode_number=catalog_ep.episode_number,
                        name=catalog_ep.name,
                        status=user_ep.status,
                        score=user_ep.score,
                    )
                )

            seasons.append(
                BackupSeasonItem(
                    season_number=catalog.season_number,
                    name=catalog.name,
                    episode_count=catalog.episode_count,
                    status=user_season.status,
                    score=user_season.score,
                    score_is_manual=user_season.score_is_manual,
                    review_text=user_season.review_text,
                    is_spoiler=user_season.is_spoiler,
                    episodes=episodes or None,
                )
            )
        return seasons

    def _export_dlc(self, user_title: UserTitle) -> BackupDlcItem:
        title = user_title.title
        return BackupDlcItem(
            external_id=title.external_id,
            title=title.name,
            poster_url=title.cover_image,
            release_year=title.release_year,
            genres=title.genres or [],
            status=user_title.status,
            score=user_title.score,
            review_text=user_title.review_text,
            is_spoiler=user_title.is_spoiler,
            finished_at=user_title.finished_at,
            times_completed=user_title.times_completed,
            is_completed_100_percent=user_title.is_completed_100_percent,
            game_platform=user_title.game_platform,
        )

    @post("/import")
    async def import_backup(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> BackupResponse:
        """Import user titles from a backup file."""
        user = request.user
        content = await data.read()
        try:
            items_data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError:
            return BackupResponse(message="Invalid JSON file", processed_count=0)

        processed_count = 0

        for item_data in items_data:
            item = BackupItem(**item_data)
            title = await self._ensure_title(
                db_session,
                external_id=item.external_id,
                category=item.type,
                name=item.title,
                poster_url=item.poster_url,
                release_year=item.release_year,
                genres=item.genres,
                parent_title_id=None,
            )
            user_title = await self._upsert_user_title(
                db_session,
                user_id=user.id,
                title_id=title.id,
                status=item.status,
                score=item.score,
                review_text=item.review_text,
                is_spoiler=item.is_spoiler,
                finished_at=item.finished_at,
                times_completed=item.times_completed,
                is_completed_100_percent=item.is_completed_100_percent,
                game_platform=item.game_platform,
                progress_value=item.progress_value,
            )

            if item.screenshots is not None:
                await self._replace_screenshots(
                    db_session, user_title, item.screenshots
                )

            if item.seasons:
                await self._import_seasons(
                    db_session, title, user_title, item.seasons
                )

            if item.dlcs:
                for dlc in item.dlcs:
                    dlc_title = await self._ensure_title(
                        db_session,
                        external_id=dlc.external_id,
                        category=TitleCategory.GAME,
                        name=dlc.title,
                        poster_url=dlc.poster_url,
                        release_year=dlc.release_year,
                        genres=dlc.genres,
                        parent_title_id=title.id,
                    )
                    await self._upsert_user_title(
                        db_session,
                        user_id=user.id,
                        title_id=dlc_title.id,
                        status=dlc.status,
                        score=dlc.score,
                        review_text=dlc.review_text,
                        is_spoiler=dlc.is_spoiler,
                        finished_at=dlc.finished_at,
                        times_completed=dlc.times_completed,
                        is_completed_100_percent=dlc.is_completed_100_percent,
                        game_platform=dlc.game_platform,
                        progress_value=None,
                    )

            processed_count += 1

        await db_session.commit()
        return BackupResponse(
            message="Backup imported successfully", processed_count=processed_count
        )

    async def _ensure_title(
        self,
        db_session: AsyncSession,
        *,
        external_id: str | None,
        category: TitleCategory,
        name: str,
        poster_url: str | None,
        release_year: int | None,
        genres: list[str] | None,
        parent_title_id: int | None,
    ) -> Title:
        existing_title = None
        if external_id:
            stmt = select(Title).where(
                Title.external_id == external_id,
                Title.category == category,
            )
            result = await db_session.execute(stmt)
            existing_title = result.scalar_one_or_none()

        if existing_title:
            if parent_title_id is not None and existing_title.parent_title_id is None:
                existing_title.parent_title_id = parent_title_id
            return existing_title

        new_title = Title(
            name=name,
            category=category,
            external_id=external_id,
            cover_image=poster_url,
            release_year=release_year,
            genres=genres,
            parent_title_id=parent_title_id,
        )
        db_session.add(new_title)
        await db_session.flush()
        return new_title

    async def _upsert_user_title(
        self,
        db_session: AsyncSession,
        *,
        user_id: int,
        title_id: int,
        status,
        score: float | None,
        review_text: str | None,
        is_spoiler: bool,
        finished_at: datetime | None,
        times_completed: int,
        is_completed_100_percent: bool,
        game_platform,
        progress_value: int | None = None,
    ) -> UserTitle:
        stmt = (
            pg_insert(UserTitle)
            .values(
                user_id=user_id,
                title_id=title_id,
                status=status,
                score=score,
                review_text=review_text,
                is_spoiler=is_spoiler,
                finished_at=finished_at,
                times_completed=times_completed,
                is_completed_100_percent=is_completed_100_percent,
                game_platform=game_platform,
                progress_value=progress_value,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "title_id"],
                set_={
                    "status": status,
                    "score": score,
                    "review_text": review_text,
                    "is_spoiler": is_spoiler,
                    "finished_at": finished_at,
                    "times_completed": times_completed,
                    "is_completed_100_percent": is_completed_100_percent,
                    "game_platform": game_platform,
                    "progress_value": progress_value,
                    "updated_at": datetime.now(),
                },
            )
            .returning(UserTitle.id)
        )
        result = await db_session.execute(stmt)
        user_title_id = result.scalar_one()
        user_title = await db_session.get(UserTitle, user_title_id)
        assert user_title is not None
        return user_title

    async def _replace_screenshots(
        self,
        db_session: AsyncSession,
        user_title: UserTitle,
        screenshots: list[str],
    ) -> None:
        await db_session.execute(
            delete(TitleScreenshot).where(
                TitleScreenshot.user_title_id == user_title.id
            )
        )

        for position, screenshot_url in enumerate(
            screenshots[:MAX_SCREENSHOTS_PER_ENTRY]
        ):
            s3_key = parse_s3_key_from_url(screenshot_url)
            if s3_key is None:
                logger.warning(
                    "Skipping screenshot at position %s for user_title %s",
                    position,
                    user_title.id,
                )
                continue
            db_session.add(
                TitleScreenshot(
                    user_title_id=user_title.id,
                    url=screenshot_url,
                    s3_key=s3_key,
                    position=position,
                )
            )

    async def _import_seasons(
        self,
        db_session: AsyncSession,
        title: Title,
        user_title: UserTitle,
        seasons: list[BackupSeasonItem],
    ) -> None:
        for season_item in seasons:
            catalog_stmt = select(TitleSeason).where(
                TitleSeason.title_id == title.id,
                TitleSeason.season_number == season_item.season_number,
            )
            catalog_result = await db_session.execute(catalog_stmt)
            title_season = catalog_result.scalar_one_or_none()
            if not title_season:
                title_season = TitleSeason(
                    title_id=title.id,
                    season_number=season_item.season_number,
                    name=season_item.name,
                    episode_count=season_item.episode_count,
                )
                db_session.add(title_season)
                await db_session.flush()
            else:
                if season_item.name is not None:
                    title_season.name = season_item.name
                if season_item.episode_count is not None:
                    title_season.episode_count = season_item.episode_count

            user_season_stmt = select(UserTitleSeason).where(
                UserTitleSeason.user_title_id == user_title.id,
                UserTitleSeason.title_season_id == title_season.id,
            )
            user_season_result = await db_session.execute(user_season_stmt)
            user_season = user_season_result.scalar_one_or_none()
            if not user_season:
                user_season = UserTitleSeason(
                    user_title_id=user_title.id,
                    title_season_id=title_season.id,
                    status=season_item.status,
                    score=season_item.score,
                    score_is_manual=season_item.score_is_manual,
                    review_text=season_item.review_text,
                    is_spoiler=season_item.is_spoiler,
                )
                db_session.add(user_season)
                await db_session.flush()
            else:
                user_season.status = season_item.status
                user_season.score = season_item.score
                user_season.score_is_manual = season_item.score_is_manual
                user_season.review_text = season_item.review_text
                user_season.is_spoiler = season_item.is_spoiler

            for ep_item in season_item.episodes or []:
                ep_stmt = select(TitleEpisode).where(
                    TitleEpisode.title_season_id == title_season.id,
                    TitleEpisode.episode_number == ep_item.episode_number,
                )
                ep_result = await db_session.execute(ep_stmt)
                title_episode = ep_result.scalar_one_or_none()
                if not title_episode:
                    title_episode = TitleEpisode(
                        title_season_id=title_season.id,
                        episode_number=ep_item.episode_number,
                        name=ep_item.name,
                    )
                    db_session.add(title_episode)
                    await db_session.flush()
                elif ep_item.name is not None:
                    title_episode.name = ep_item.name

                user_ep_stmt = select(UserTitleEpisode).where(
                    UserTitleEpisode.user_title_season_id == user_season.id,
                    UserTitleEpisode.title_episode_id == title_episode.id,
                )
                user_ep_result = await db_session.execute(user_ep_stmt)
                user_episode = user_ep_result.scalar_one_or_none()
                if not user_episode:
                    db_session.add(
                        UserTitleEpisode(
                            user_title_season_id=user_season.id,
                            title_episode_id=title_episode.id,
                            status=ep_item.status,
                            score=ep_item.score,
                        )
                    )
                else:
                    user_episode.status = ep_item.status
                    user_episode.score = ep_item.score

            if season_item.episodes:
                title_season.episode_count = max(
                    title_season.episode_count or 0,
                    max(ep.episode_number for ep in season_item.episodes),
                )
