from typing import Annotated, Any, Literal

from sqlalchemy import select, or_, func, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from litestar import Controller, get, post, patch, delete as litestar_delete, Request
from litestar.di import Provide
from litestar.params import Parameter, Body
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException, NotFoundException
from litestar.security.jwt import Token

from core.models.db_helper import get_db_session
from core.models import Title, User, UserTitle, UserTitleStatus
from core.models.user import subscriptions_table
from core.models.notification import Notification, NotificationType
from core.privacy import ensure_can_view_user_library
from titles.schemas import TitleRead
from .schemas import UserRead, UserProfileRead, UserProfileUpdate, FollowStatusResponse
from .compare_schemas import (
    LibraryCompareCounts,
    LibraryCompareItem,
    LibraryCompareResponse,
    LibraryCompareSide,
)


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
            bio=user.bio,
            is_private=user.is_private,
            followers_count=followers_count,
            following_count=following_count,
            is_following=is_following,
        )

    @patch("/me")
    async def update_me(
        self,
        data: UserProfileUpdate,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
    ) -> UserRead:
        """Update current user's profile fields."""
        user = request.user
        payload = data.model_dump(exclude_unset=True)

        if "name" in payload:
            user.name = payload["name"]
        if "bio" in payload:
            user.bio = payload["bio"]
        if "is_private" in payload and payload["is_private"] is not None:
            user.is_private = payload["is_private"]

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return UserRead.model_validate(user)

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

        # Notify the followed user
        notification = Notification(
            recipient_id=user_id,
            actor_id=current_user_id,
            user_title_id=None,
            type=NotificationType.NEW_FOLLOWER,
        )
        db_session.add(notification)

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

    @get("/{user_id:int}/compare")
    async def compare_libraries(
        self,
        user_id: int,
        request: Request[User, Token, Any],
        db_session: AsyncSession,
        bucket: Literal[
            "both_completed", "only_me", "only_them", "both_other"
        ] = "both_completed",
        limit: int = 50,
        offset: int = 0,
    ) -> LibraryCompareResponse:
        """Compare current user's library with another user's."""
        if user_id == request.user.id:
            raise HTTPException(detail="Cannot compare with yourself", status_code=400)

        other = await db_session.get(User, user_id)
        if not other:
            raise NotFoundException(detail="User not found")

        await ensure_can_view_user_library(user_id, request.user.id, db_session)

        async def load_library(uid: int) -> dict[int, UserTitle]:
            stmt = (
                select(UserTitle)
                .join(Title, Title.id == UserTitle.title_id)
                .options(selectinload(UserTitle.title))
                .where(
                    UserTitle.user_id == uid,
                    Title.parent_title_id.is_(None),
                )
            )
            result = await db_session.execute(stmt)
            return {ut.title_id: ut for ut in result.scalars().unique().all()}

        mine = await load_library(request.user.id)
        theirs = await load_library(user_id)

        both_completed: list[int] = []
        only_me: list[int] = []
        only_them: list[int] = []
        both_other: list[int] = []

        all_ids = set(mine) | set(theirs)
        for title_id in all_ids:
            my_ut = mine.get(title_id)
            their_ut = theirs.get(title_id)
            if my_ut and their_ut:
                if (
                    my_ut.status == UserTitleStatus.COMPLETED
                    and their_ut.status == UserTitleStatus.COMPLETED
                ):
                    both_completed.append(title_id)
                else:
                    both_other.append(title_id)
            elif my_ut:
                only_me.append(title_id)
            else:
                only_them.append(title_id)

        counts = LibraryCompareCounts(
            both_completed=len(both_completed),
            only_me=len(only_me),
            only_them=len(only_them),
            both_other=len(both_other),
        )

        bucket_map = {
            "both_completed": both_completed,
            "only_me": only_me,
            "only_them": only_them,
            "both_other": both_other,
        }
        selected_ids = bucket_map[bucket]

        def sort_key(tid: int) -> str:
            ut = mine.get(tid) or theirs.get(tid)
            return (ut.title.name if ut else "").lower()

        selected_ids = sorted(selected_ids, key=sort_key)
        page_ids = selected_ids[offset : offset + min(limit, 100)]

        def side(ut: UserTitle | None) -> LibraryCompareSide:
            if not ut:
                return LibraryCompareSide()
            status = ut.status.value if hasattr(ut.status, "value") else str(ut.status)
            return LibraryCompareSide(
                status=status,
                score=ut.score,
                user_title_id=ut.id,
            )

        items: list[LibraryCompareItem] = []
        for tid in page_ids:
            my_ut = mine.get(tid)
            their_ut = theirs.get(tid)
            title = (my_ut or their_ut).title  # type: ignore[union-attr]
            items.append(
                LibraryCompareItem(
                    title=TitleRead.model_validate(title),
                    me=side(my_ut),
                    them=side(their_ut),
                )
            )

        return LibraryCompareResponse(
            other_user=UserRead.model_validate(other),
            counts=counts,
            bucket=bucket,
            items=items,
        )

    @get("/{user_id:int}/followers")
    async def get_followers(
        self,
        user_id: int,
        db_session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserRead]:
        """Get list of users who follow this user."""
        stmt = (
            select(User)
            .join(
                subscriptions_table,
                subscriptions_table.c.follower_id == User.id,
            )
            .where(subscriptions_table.c.following_id == user_id)
            .limit(limit)
            .offset(offset)
        )
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        return [UserRead.model_validate(u) for u in users]

    @get("/{user_id:int}/following")
    async def get_following(
        self,
        user_id: int,
        db_session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserRead]:
        """Get list of users this user follows."""
        stmt = (
            select(User)
            .join(
                subscriptions_table,
                subscriptions_table.c.following_id == User.id,
            )
            .where(subscriptions_table.c.follower_id == user_id)
            .limit(limit)
            .offset(offset)
        )
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        return [UserRead.model_validate(u) for u in users]

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
