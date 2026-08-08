"""Build DLC list responses for a game UserTitle."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Title, UserTitle
from .dlc_sync import sync_dlcs_from_igdb
from .schemas import DlcItemRead, GameDlcsRead


async def build_game_dlcs_response(
    db_session: AsyncSession,
    user_title: UserTitle,
    *,
    sync: bool = True,
) -> GameDlcsRead:
    if sync:
        catalog_dlcs = await sync_dlcs_from_igdb(db_session, user_title.title)
    else:
        catalog_stmt = (
            select(Title)
            .where(Title.parent_title_id == user_title.title_id)
            .order_by(Title.release_year.asc().nulls_last(), Title.name.asc())
        )
        catalog_result = await db_session.execute(catalog_stmt)
        catalog_dlcs = list(catalog_result.scalars().all())

    dlc_title_ids = [t.id for t in catalog_dlcs]
    user_by_title_id: dict[int, UserTitle] = {}
    if dlc_title_ids:
        user_stmt = select(UserTitle).where(
            UserTitle.user_id == user_title.user_id,
            UserTitle.title_id.in_(dlc_title_ids),
        )
        user_result = await db_session.execute(user_stmt)
        for ut in user_result.scalars().all():
            user_by_title_id[ut.title_id] = ut

    items: list[DlcItemRead] = []
    for dlc_title in catalog_dlcs:
        user_dlc = user_by_title_id.get(dlc_title.id)
        items.append(
            DlcItemRead(
                title_id=dlc_title.id,
                external_id=dlc_title.external_id,
                name=dlc_title.name,
                cover_image=dlc_title.cover_image,
                release_year=dlc_title.release_year,
                user_title_id=user_dlc.id if user_dlc else None,
                status=user_dlc.status if user_dlc else None,
                score=user_dlc.score if user_dlc else None,
                review_text=user_dlc.review_text if user_dlc else None,
                is_spoiler=user_dlc.is_spoiler if user_dlc else False,
            )
        )

    return GameDlcsRead(
        user_title_id=user_title.id,
        title_id=user_title.title_id,
        dlcs=items,
    )
