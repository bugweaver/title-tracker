"""Recalculate season/series average scores after episode or season changes."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Title, TitleSeason, UserTitle, UserTitleEpisode, UserTitleSeason


def _average(scores: list[float]) -> float | None:
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


async def recalc_season_from_episodes(
    db_session: AsyncSession,
    user_title_season: UserTitleSeason,
) -> None:
    """Update season avg_score from episode scores; apply to score unless manual."""
    stmt = select(UserTitleEpisode).where(
        UserTitleEpisode.user_title_season_id == user_title_season.id
    )
    result = await db_session.execute(stmt)
    episodes = result.scalars().all()
    scores = [ep.score for ep in episodes if ep.score is not None]
    avg = _average(scores)
    user_title_season.avg_score = avg
    if not user_title_season.score_is_manual:
        user_title_season.score = avg


async def recalc_series_from_seasons(
    db_session: AsyncSession,
    user_title: UserTitle,
) -> None:
    """Update series avg_score from season scores; apply to score unless manual."""
    stmt = select(UserTitleSeason).where(
        UserTitleSeason.user_title_id == user_title.id
    )
    result = await db_session.execute(stmt)
    seasons = result.scalars().all()
    scores = [s.score for s in seasons if s.score is not None]
    avg = _average(scores)
    user_title.avg_score = avg
    if not user_title.score_is_manual:
        user_title.score = avg


async def cascade_after_episode_change(
    db_session: AsyncSession,
    user_title_season: UserTitleSeason,
) -> UserTitle:
    await recalc_season_from_episodes(db_session, user_title_season)
    await db_session.flush()

    stmt = select(UserTitle).where(UserTitle.id == user_title_season.user_title_id)
    result = await db_session.execute(stmt)
    user_title = result.scalar_one()
    await recalc_series_from_seasons(db_session, user_title)
    await db_session.flush()
    return user_title


async def cascade_after_season_change(
    db_session: AsyncSession,
    user_title_season: UserTitleSeason,
) -> UserTitle:
    stmt = select(UserTitle).where(UserTitle.id == user_title_season.user_title_id)
    result = await db_session.execute(stmt)
    user_title = result.scalar_one()
    await recalc_series_from_seasons(db_session, user_title)
    await db_session.flush()
    return user_title


async def reset_series_score_to_avg(
    db_session: AsyncSession,
    user_title: UserTitle,
) -> UserTitle:
    await recalc_series_from_seasons(db_session, user_title)
    user_title.score_is_manual = False
    user_title.score = user_title.avg_score
    await db_session.flush()
    return user_title


async def reset_season_score_to_avg(
    db_session: AsyncSession,
    user_title_season: UserTitleSeason,
) -> UserTitle:
    await recalc_season_from_episodes(db_session, user_title_season)
    user_title_season.score_is_manual = False
    user_title_season.score = user_title_season.avg_score
    await db_session.flush()
    return await cascade_after_season_change(db_session, user_title_season)


async def load_user_title_with_structure(
    db_session: AsyncSession,
    user_title_id: int,
) -> UserTitle | None:
    stmt = (
        select(UserTitle)
        .options(
            selectinload(UserTitle.title)
            .selectinload(Title.seasons)
            .selectinload(TitleSeason.episodes),
            selectinload(UserTitle.seasons)
            .selectinload(UserTitleSeason.title_season)
            .selectinload(TitleSeason.episodes),
            selectinload(UserTitle.seasons)
            .selectinload(UserTitleSeason.episodes)
            .selectinload(UserTitleEpisode.title_episode),
        )
        .where(UserTitle.id == user_title_id)
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()
