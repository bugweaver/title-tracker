"""Sync game DLC/expansion catalog titles from IGDB."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.igdb_service import igdb_service
from core.models import Title, TitleCategory


async def sync_dlcs_from_igdb(db_session: AsyncSession, parent_title: Title) -> list[Title]:
    """Fetch DLC/expansions for a game and upsert them as child Title rows."""
    if parent_title.category != TitleCategory.GAME or not parent_title.external_id:
        return []

    try:
        dlc_games = await igdb_service.get_game_dlcs(parent_title.external_id)
    except Exception:
        return []

    if not dlc_games:
        # Still return existing children linked in DB
        existing_stmt = (
            select(Title)
            .where(Title.parent_title_id == parent_title.id)
            .order_by(Title.release_year.asc().nulls_last(), Title.name.asc())
        )
        existing_result = await db_session.execute(existing_stmt)
        return list(existing_result.scalars().all())

    prior_stmt = select(Title.id).where(Title.parent_title_id == parent_title.id).limit(1)
    prior_result = await db_session.execute(prior_stmt)
    had_prior_dlcs = prior_result.scalar_one_or_none() is not None

    synced: list[Title] = []
    had_new_dlc = False
    for game in dlc_games:
        external_id = str(game["id"])
        stmt = select(Title).where(
            Title.external_id == external_id,
            Title.category == TitleCategory.GAME,
        )
        result = await db_session.execute(stmt)
        title = result.scalar_one_or_none()

        if title:
            title.parent_title_id = parent_title.id
            if game.get("name"):
                title.name = game["name"]
            if game.get("cover_url"):
                title.cover_image = game["cover_url"]
            if game.get("release_year"):
                title.release_year = game["release_year"]
            if game.get("genres"):
                title.genres = game["genres"]
        else:
            title = Title(
                name=game["name"],
                category=TitleCategory.GAME,
                external_id=external_id,
                cover_image=game.get("cover_url"),
                release_year=game.get("release_year"),
                genres=game.get("genres") or [],
                parent_title_id=parent_title.id,
            )
            db_session.add(title)
            had_new_dlc = True

        synced.append(title)

    await db_session.flush()

    if had_new_dlc and had_prior_dlcs:
        from notifications.reminders import notify_title_owners_of_new_release

        await notify_title_owners_of_new_release(db_session, parent_title.id)

    # Include any previously linked children that IGDB no longer returns
    existing_stmt = (
        select(Title)
        .where(Title.parent_title_id == parent_title.id)
        .order_by(Title.release_year.asc().nulls_last(), Title.name.asc())
    )
    existing_result = await db_session.execute(existing_stmt)
    return list(existing_result.scalars().all())
