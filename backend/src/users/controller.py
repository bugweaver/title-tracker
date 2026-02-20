from typing import Annotated, Any

from sqlalchemy import select, or_, func, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from litestar import Controller, get, post, delete as litestar_delete, Request
from litestar.di import Provide
from litestar.params import Parameter, Body
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException

from core.models.db_helper import get_db_session
from core.models import User
from core.models.user import subscriptions_table
from .schemas import UserRead, UserProfileRead, FollowStatusResponse


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
        stmt = select(User).limit(limit).offset(offset)
        
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
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> UserProfileRead:
        """Get user profile by ID with follower/following counts."""
        user = await db_session.get(User, user_id)
        if not user:
            raise NotFoundException(detail="User not found")

        # Follower count
        follower_count_stmt = select(func.count()).select_from(subscriptions_table).where(
            subscriptions_table.c.following_id == user_id
        )
        follower_result = await db_session.execute(follower_count_stmt)
        followers_count = follower_result.scalar() or 0

        # Following count
        following_count_stmt = select(func.count()).select_from(subscriptions_table).where(
            subscriptions_table.c.follower_id == user_id
        )
        following_result = await db_session.execute(following_count_stmt)
        following_count = following_result.scalar() or 0

        # Is current user following this user?
        is_following = False
        if request.user.id != user_id:
            follow_check = select(func.count()).select_from(subscriptions_table).where(
                subscriptions_table.c.follower_id == request.user.id,
                subscriptions_table.c.following_id == user_id,
            )
            check_result = await db_session.execute(follow_check)
            is_following = (check_result.scalar() or 0) > 0

        return UserProfileRead(
            id=user.id,
            login=user.login,
            name=user.name,
            avatar_url=user.avatar_url,
            followers_count=followers_count,
            following_count=following_count,
            is_following=is_following,
        )

    @post("/{user_id:int}/follow")
    async def follow_user(
        self,
        user_id: int,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> FollowStatusResponse:
        """Follow a user."""
        current_user_id = request.user.id

        if current_user_id == user_id:
            from litestar.exceptions import ClientException
            raise ClientException(detail="Cannot follow yourself", status_code=400)

        # Check if target user exists
        target = await db_session.get(User, user_id)
        if not target:
            raise NotFoundException(detail="User not found")

        # Check if already following
        check_stmt = select(func.count()).select_from(subscriptions_table).where(
            subscriptions_table.c.follower_id == current_user_id,
            subscriptions_table.c.following_id == user_id,
        )
        result = await db_session.execute(check_stmt)
        if (result.scalar() or 0) > 0:
            return FollowStatusResponse(is_following=True)

        # Insert subscription
        stmt = insert(subscriptions_table).values(
            follower_id=current_user_id,
            following_id=user_id,
        )
        await db_session.execute(stmt)
        await db_session.commit()

        return FollowStatusResponse(is_following=True)

    @litestar_delete("/{user_id:int}/follow", status_code=200)
    async def unfollow_user(
        self,
        user_id: int,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> FollowStatusResponse:
        """Unfollow a user."""
        current_user_id = request.user.id

        stmt = delete(subscriptions_table).where(
            subscriptions_table.c.follower_id == current_user_id,
            subscriptions_table.c.following_id == user_id,
        )
        await db_session.execute(stmt)
        await db_session.commit()

        return FollowStatusResponse(is_following=False)

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
        
        static_dir = os.path.join(os.getcwd(), "static", "avatars")
        os.makedirs(static_dir, exist_ok=True)
        
        ext = avatar.filename.split('.')[-1] if '.' in avatar.filename else 'png'
        filename = f"user_{user_id}_{uuid4().hex}.{ext}"
        file_path = os.path.join(static_dir, filename)
        
        content = await avatar.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        request.user.avatar_url = f"/static/avatars/{filename}"
        
        db_session.add(request.user)
        await db_session.commit()
        await db_session.refresh(request.user)
        
        return UserRead.model_validate(request.user)
