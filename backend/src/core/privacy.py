from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from litestar.exceptions import HTTPException, NotFoundException

from core.models import User
from core.models.user import subscriptions_table


async def ensure_can_view_user_library(
    owner_id: int,
    viewer_id: int,
    db_session: AsyncSession,
) -> None:
    if owner_id == viewer_id:
        return

    owner = await db_session.get(User, owner_id)
    if not owner:
        raise NotFoundException(detail="User not found")
    if not owner.is_private:
        return

    follow_check = select(func.count()).select_from(subscriptions_table).where(
        subscriptions_table.c.follower_id == viewer_id,
        subscriptions_table.c.following_id == owner_id,
    )
    result = await db_session.execute(follow_check)
    if (result.scalar() or 0) == 0:
        raise HTTPException(detail="Профиль закрыт", status_code=403)
