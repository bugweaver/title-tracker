"""Sync series season/episode catalog from TMDB into local tables."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Title, TitleCategory, TitleEpisode, TitleSeason, UserTitle
from core.tmdb_service import TmdbService


async def sync_seasons_from_tmdb(
    db_session: AsyncSession,
    title: Title,
) -> list[TitleSeason]:
    """Upsert title_seasons from TMDB (excludes season 0)."""
    if title.category != TitleCategory.SERIES or not title.external_id:
        return []

    tmdb = TmdbService("tv")
    seasons_data = await tmdb.get_tv_seasons(title.external_id)
    if not seasons_data:
        # Fall back to whatever is already stored
        stmt = (
            select(TitleSeason)
            .where(TitleSeason.title_id == title.id)
            .order_by(TitleSeason.season_number)
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    existing_stmt = select(TitleSeason).where(TitleSeason.title_id == title.id)
    existing_result = await db_session.execute(existing_stmt)
    existing = {s.season_number: s for s in existing_result.scalars().all()}

    synced: list[TitleSeason] = []
    for item in seasons_data:
        season_number = item["season_number"]
        season = existing.get(season_number)
        if season:
            season.name = item.get("name")
            season.episode_count = item.get("episode_count")
        else:
            season = TitleSeason(
                title_id=title.id,
                season_number=season_number,
                name=item.get("name"),
                episode_count=item.get("episode_count"),
            )
            db_session.add(season)
        synced.append(season)

    await db_session.flush()
    return sorted(synced, key=lambda s: s.season_number)


async def sync_season_episodes_from_tmdb(
    db_session: AsyncSession,
    title: Title,
    title_season: TitleSeason,
) -> list[TitleEpisode]:
    """Upsert episodes for a season from TMDB."""
    if title.category != TitleCategory.SERIES or not title.external_id:
        return list(title_season.episodes or [])

    tmdb = TmdbService("tv")
    episodes_data = await tmdb.get_season_episodes(
        title.external_id, title_season.season_number
    )
    if episodes_data is None:
        return list(title_season.episodes or [])

    existing_stmt = select(TitleEpisode).where(
        TitleEpisode.title_season_id == title_season.id
    )
    existing_result = await db_session.execute(existing_stmt)
    existing = {e.episode_number: e for e in existing_result.scalars().all()}

    synced: list[TitleEpisode] = []
    for item in episodes_data:
        episode_number = item["episode_number"]
        episode = existing.get(episode_number)
        if episode:
            episode.name = item.get("name")
        else:
            episode = TitleEpisode(
                title_season_id=title_season.id,
                episode_number=episode_number,
                name=item.get("name"),
            )
            db_session.add(episode)
        synced.append(episode)

    title_season.episode_count = len(synced)
    await db_session.flush()
    return sorted(synced, key=lambda e: e.episode_number)


async def sync_full_structure(
    db_session: AsyncSession,
    user_title: UserTitle,
    *,
    load_all_episodes: bool = False,
) -> UserTitle:
    """Sync seasons (and optionally all episodes) for a series user title."""
    stmt = (
        select(Title)
        .options(selectinload(Title.seasons).selectinload(TitleSeason.episodes))
        .where(Title.id == user_title.title_id)
    )
    result = await db_session.execute(stmt)
    title = result.scalar_one()

    seasons = await sync_seasons_from_tmdb(db_session, title)
    if load_all_episodes:
        for season in seasons:
            await sync_season_episodes_from_tmdb(db_session, title, season)

    await db_session.flush()
    return user_title
