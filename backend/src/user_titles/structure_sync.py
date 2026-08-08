"""Sync series/anime season/episode catalog into local tables."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Title, TitleCategory, TitleEpisode, TitleSeason, UserTitle
from core.shikimori_service import ShikimoriService
from core.tmdb_service import TmdbService

STRUCTURE_CATEGORIES = frozenset({TitleCategory.SERIES, TitleCategory.ANIME})


def supports_structure(category: TitleCategory | str | None) -> bool:
    if category is None:
        return False
    value = category.value if isinstance(category, TitleCategory) else str(category)
    return value in {c.value for c in STRUCTURE_CATEGORIES}


async def _fetch_seasons(title: Title) -> list[dict[str, Any]]:
    if not title.external_id:
        return []
    if title.category == TitleCategory.SERIES:
        return await TmdbService("tv").get_tv_seasons(title.external_id)
    if title.category == TitleCategory.ANIME:
        return await ShikimoriService("anime").get_anime_seasons(title.external_id)
    return []


async def _fetch_episodes(
    title: Title, season_number: int
) -> list[dict[str, Any]] | None:
    if not title.external_id:
        return None
    if title.category == TitleCategory.SERIES:
        return await TmdbService("tv").get_season_episodes(
            title.external_id, season_number
        )
    if title.category == TitleCategory.ANIME:
        return await ShikimoriService("anime").get_season_episodes(
            title.external_id, season_number
        )
    return None


async def sync_seasons_from_tmdb(
    db_session: AsyncSession,
    title: Title,
) -> list[TitleSeason]:
    """Upsert title_seasons from the provider (TMDB for series, Shikimori for anime)."""
    if not supports_structure(title.category) or not title.external_id:
        return []

    seasons_data = await _fetch_seasons(title)
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
    had_new_season = False
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
            had_new_season = True
        synced.append(season)

    await db_session.flush()

    if had_new_season and existing:
        from notifications.reminders import notify_title_owners_of_new_release

        await notify_title_owners_of_new_release(db_session, title.id)

    return sorted(synced, key=lambda s: s.season_number)


async def sync_season_episodes_from_tmdb(
    db_session: AsyncSession,
    title: Title,
    title_season: TitleSeason,
) -> list[TitleEpisode]:
    """Upsert episodes for a season from the provider."""
    if not supports_structure(title.category) or not title.external_id:
        return list(title_season.episodes or [])

    episodes_data = await _fetch_episodes(title, title_season.season_number)
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
    # TitleSeason.episodes uses selectin; if it was already loaded as empty
    # before inserts, re-reads in the same session would otherwise stay empty.
    db_session.expire(title_season, ["episodes"])
    await db_session.refresh(title_season, attribute_names=["episodes"])
    return sorted(title_season.episodes, key=lambda e: e.episode_number)


async def sync_full_structure(
    db_session: AsyncSession,
    user_title: UserTitle,
    *,
    load_all_episodes: bool = False,
) -> UserTitle:
    """Sync seasons (and optionally all episodes) for a series/anime user title."""
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
