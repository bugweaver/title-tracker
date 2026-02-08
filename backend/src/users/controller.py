from typing import Annotated, Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from litestar import Controller, get, post, Request
from litestar.di import Provide
from litestar.params import Parameter, Body
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType

from core.models.db_helper import get_db_session
from core.models import User
from .schemas import UserRead


class UsersController(Controller):
    path = "/users"
    tags = ["Users"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/")
    async def get_users(
        self,
        request: Request[User, dict, Any],  # type: ignore
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        search: Annotated[str | None, Parameter(required=False)] = None,
    ) -> list[UserRead]:
        """Get list of users with optional search."""
        # Start query
        stmt = select(User).limit(limit).offset(offset)
        
        # Base filter: Exclude current user
        current_user_id = request.user.id
        filters = [User.id != current_user_id]

        if search:
            filters.append(
                or_(
                    User.login.ilike(f"%{search}%"),
                    User.name.ilike(f"%{search}%")
                )
            )
            
        stmt = stmt.where(*filters)
            
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        
        return [UserRead.model_validate(u) for u in users]
    @get("/{user_id:int}")
    async def get_user(
        self,
        user_id: int,
        db_session: AsyncSession,
    ) -> UserRead:
        """Get user by ID."""
        user = await db_session.get(User, user_id)
        if not user:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(detail="User not found")
            
        return UserRead.model_validate(user)

    @post("/me/avatar")
    async def upload_avatar(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> UserRead:
        """Upload user avatar."""
        import os
        from uuid import uuid4
        
        user_id = request.user.id
        avatar = data
        
        # Create directory if not exists
        static_dir = os.path.join(os.getcwd(), "static", "avatars")
        os.makedirs(static_dir, exist_ok=True)
        
        # Create unique filename
        ext = avatar.filename.split('.')[-1] if '.' in avatar.filename else 'png'
        filename = f"user_{user_id}_{uuid4().hex}.{ext}"
        file_path = os.path.join(static_dir, filename)
        
        # Save file
        content = await avatar.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        # Update user
        # We need a way to serve this. 
        # Ideally, we should use a full URL or a path relative to root that frontend can use.
        # user.avatar_url = f"/static/avatars/{filename}"
        request.user.avatar_url = f"/static/avatars/{filename}"
        
        db_session.add(request.user)
        await db_session.commit()
        await db_session.refresh(request.user)
        
        return UserRead.model_validate(request.user)
