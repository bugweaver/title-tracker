from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from litestar import Controller, get, post, Request
from litestar.di import Provide
from litestar.security.jwt import Token

from core.models.db_helper import get_db_session
from core.models import User, Title, UserTitle
from .schemas import TitleCreate, TitleRead, UserTitleRead, UserTitleCreate


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
        return await self._get_titles_for_user(request.user.id, db_session)

    @get("/user/{user_id:int}")
    async def get_user_titles(
        self, user_id: int, db_session: AsyncSession
    ) -> list[UserTitleRead]:
        """Get public titles for a specific user."""
        return await self._get_titles_for_user(user_id, db_session)

    async def _get_titles_for_user(self, user_id: int, db_session: AsyncSession) -> list[UserTitleRead]:
        stmt = (
            select(UserTitle)
            .options(selectinload(UserTitle.title))
            .where(UserTitle.user_id == user_id)
            .order_by(UserTitle.updated_at.desc())
        )
        
        result = await db_session.execute(stmt)
        user_titles = result.scalars().all()
        
        return [UserTitleRead.model_validate(ut) for ut in user_titles]

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
        db_session: AsyncSession
    ) -> UserTitleRead:
        """Add a title to the current user's list."""
        user_id = request.user.id
        
        user_title = UserTitle(
            user_id=user_id,
            title_id=data.title_id,
            status=data.status,
            score=data.score
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
