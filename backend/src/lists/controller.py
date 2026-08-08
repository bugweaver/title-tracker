from typing import Any

from litestar import Controller, Request, delete, get, patch, post, put
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import User, UserList, UserListItem, UserTitle
from core.models.db_helper import get_db_session
from titles.schemas import TitleRead

from .schemas import (
    UserListCreate,
    UserListDetail,
    UserListItemCreate,
    UserListItemRead,
    UserListReorderRequest,
    UserListSummary,
    UserListUpdate,
)


async def _get_owned_list(
    db_session: AsyncSession,
    list_id: int,
    user_id: int,
    *,
    with_items: bool = False,
) -> UserList:
    stmt = select(UserList).where(UserList.id == list_id)
    if with_items:
        stmt = stmt.options(
            selectinload(UserList.items)
            .selectinload(UserListItem.user_title)
            .selectinload(UserTitle.title)
        )
    result = await db_session.execute(stmt)
    user_list = result.scalar_one_or_none()
    if not user_list or user_list.user_id != user_id:
        raise NotFoundException(detail="List not found")
    return user_list


def _serialize_item(item: UserListItem) -> UserListItemRead:
    ut = item.user_title
    return UserListItemRead(
        id=item.id,
        user_title_id=item.user_title_id,
        position=item.position,
        status=ut.status,
        score=ut.score,
        progress_value=ut.progress_value,
        title=TitleRead.model_validate(ut.title),
    )


class ListsController(Controller):
    path = "/lists"
    tags = ["Lists"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/")
    async def list_lists(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> list[UserListSummary]:
        counts_stmt = (
            select(
                UserListItem.list_id,
                func.count(UserListItem.id).label("items_count"),
            )
            .group_by(UserListItem.list_id)
        )
        counts_result = await db_session.execute(counts_stmt)
        counts = {row.list_id: row.items_count for row in counts_result}

        stmt = (
            select(UserList)
            .where(UserList.user_id == request.user.id)
            .order_by(UserList.updated_at.desc())
        )
        result = await db_session.execute(stmt)
        lists = list(result.scalars().all())
        return [
            UserListSummary(
                id=ul.id,
                name=ul.name,
                items_count=counts.get(ul.id, 0),
                created_at=ul.created_at,
                updated_at=ul.updated_at,
            )
            for ul in lists
        ]

    @post("/")
    async def create_list(
        self,
        request: Request[User, dict, Any],
        data: UserListCreate,
        db_session: AsyncSession,
    ) -> UserListSummary:
        name = data.name.strip()
        if not name:
            raise HTTPException(detail="Name is required", status_code=400)

        user_list = UserList(user_id=request.user.id, name=name)
        db_session.add(user_list)
        await db_session.commit()
        await db_session.refresh(user_list)
        return UserListSummary(
            id=user_list.id,
            name=user_list.name,
            items_count=0,
            created_at=user_list.created_at,
            updated_at=user_list.updated_at,
        )

    @get("/{list_id:int}")
    async def get_list(
        self,
        request: Request[User, dict, Any],
        list_id: int,
        db_session: AsyncSession,
    ) -> UserListDetail:
        user_list = await _get_owned_list(
            db_session, list_id, request.user.id, with_items=True
        )
        items = sorted(user_list.items, key=lambda i: i.position)
        return UserListDetail(
            id=user_list.id,
            name=user_list.name,
            created_at=user_list.created_at,
            updated_at=user_list.updated_at,
            items=[_serialize_item(item) for item in items],
        )

    @patch("/{list_id:int}")
    async def rename_list(
        self,
        request: Request[User, dict, Any],
        list_id: int,
        data: UserListUpdate,
        db_session: AsyncSession,
    ) -> UserListSummary:
        user_list = await _get_owned_list(db_session, list_id, request.user.id)
        name = data.name.strip()
        if not name:
            raise HTTPException(detail="Name is required", status_code=400)
        user_list.name = name
        await db_session.commit()
        await db_session.refresh(user_list)

        count_stmt = select(func.count(UserListItem.id)).where(
            UserListItem.list_id == user_list.id
        )
        count_result = await db_session.execute(count_stmt)
        items_count = count_result.scalar() or 0

        return UserListSummary(
            id=user_list.id,
            name=user_list.name,
            items_count=items_count,
            created_at=user_list.created_at,
            updated_at=user_list.updated_at,
        )

    @delete("/{list_id:int}", status_code=204)
    async def delete_list(
        self,
        request: Request[User, dict, Any],
        list_id: int,
        db_session: AsyncSession,
    ) -> None:
        user_list = await _get_owned_list(db_session, list_id, request.user.id)
        await db_session.delete(user_list)
        await db_session.commit()

    @post("/{list_id:int}/items")
    async def add_item(
        self,
        request: Request[User, dict, Any],
        list_id: int,
        data: UserListItemCreate,
        db_session: AsyncSession,
    ) -> UserListDetail:
        user_list = await _get_owned_list(db_session, list_id, request.user.id)

        ut_stmt = select(UserTitle).where(
            UserTitle.id == data.user_title_id,
            UserTitle.user_id == request.user.id,
        )
        ut_result = await db_session.execute(ut_stmt)
        user_title = ut_result.scalar_one_or_none()
        if not user_title:
            raise NotFoundException(detail="Title not found in your library")

        existing_stmt = select(UserListItem).where(
            UserListItem.list_id == list_id,
            UserListItem.user_title_id == data.user_title_id,
        )
        existing_result = await db_session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise HTTPException(detail="Already in this list", status_code=400)

        max_pos_stmt = select(func.coalesce(func.max(UserListItem.position), -1)).where(
            UserListItem.list_id == list_id
        )
        max_pos_result = await db_session.execute(max_pos_stmt)
        next_pos = (max_pos_result.scalar() or -1) + 1

        db_session.add(
            UserListItem(
                list_id=list_id,
                user_title_id=data.user_title_id,
                position=next_pos,
            )
        )
        await db_session.commit()

        return await self.get_list(request, list_id, db_session)

    @delete("/{list_id:int}/items/{user_title_id:int}", status_code=204)
    async def remove_item(
        self,
        request: Request[User, dict, Any],
        list_id: int,
        user_title_id: int,
        db_session: AsyncSession,
    ) -> None:
        await _get_owned_list(db_session, list_id, request.user.id)

        stmt = select(UserListItem).where(
            UserListItem.list_id == list_id,
            UserListItem.user_title_id == user_title_id,
        )
        result = await db_session.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException(detail="Item not found in list")

        await db_session.delete(item)
        await db_session.commit()

    @put("/{list_id:int}/reorder")
    async def reorder_items(
        self,
        request: Request[User, dict, Any],
        list_id: int,
        data: UserListReorderRequest,
        db_session: AsyncSession,
    ) -> UserListDetail:
        user_list = await _get_owned_list(
            db_session, list_id, request.user.id, with_items=True
        )
        items_by_ut = {item.user_title_id: item for item in user_list.items}

        if set(data.user_title_ids) != set(items_by_ut.keys()):
            raise HTTPException(
                detail="Reorder payload must include exactly the list items",
                status_code=400,
            )

        for position, user_title_id in enumerate(data.user_title_ids):
            items_by_ut[user_title_id].position = position

        await db_session.commit()
        return await self.get_list(request, list_id, db_session)
