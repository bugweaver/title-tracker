from typing import Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from litestar import Controller, get, patch, Request
from litestar.di import Provide
from litestar.exceptions import NotFoundException

from core.models.db_helper import get_db_session
from core.models import User
from core.models.notification import Notification
from core.models.title import UserTitle
from .schemas import NotificationRead, UnreadCountResponse, ActorInfo, TitleInfo


def _build_notification_query():
    """Build base query with all needed joins."""
    return (
        select(Notification)
        .options(
            selectinload(Notification.actor),
            selectinload(Notification.user_title).selectinload(UserTitle.title),
        )
    )


def _serialize_notification(n: Notification) -> NotificationRead:
    title_info = None
    if n.user_title and n.user_title.title:
        title_info = TitleInfo.model_validate(n.user_title.title)

    return NotificationRead(
        id=n.id,
        type=n.type,
        is_read=n.is_read,
        created_at=n.created_at,
        user_title_id=n.user_title_id,
        actor=ActorInfo.model_validate(n.actor),
        title=title_info,
    )


class NotificationsController(Controller):
    path = "/notifications"
    tags = ["Notifications"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/")
    async def get_notifications(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
        limit: int = 30,
        offset: int = 0,
    ) -> list[NotificationRead]:
        """Get notifications for the current user."""
        stmt = (
            _build_notification_query()
            .where(Notification.recipient_id == request.user.id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db_session.execute(stmt)
        notifications = result.scalars().all()
        return [_serialize_notification(n) for n in notifications]

    @get("/unread-count")
    async def get_unread_count(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> UnreadCountResponse:
        """Get the number of unread notifications."""
        stmt = (
            select(func.count(Notification.id))
            .where(
                Notification.recipient_id == request.user.id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        result = await db_session.execute(stmt)
        count = result.scalar() or 0
        return UnreadCountResponse(count=count)

    @patch("/{notification_id:int}/read")
    async def mark_as_read(
        self,
        notification_id: int,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> NotificationRead:
        """Mark a single notification as read."""
        stmt = (
            _build_notification_query()
            .where(
                Notification.id == notification_id,
                Notification.recipient_id == request.user.id,
            )
        )
        result = await db_session.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            raise NotFoundException(detail="Notification not found")

        notification.is_read = True
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)

        return _serialize_notification(notification)

    @patch("/read-all")
    async def mark_all_as_read(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> dict[str, str]:
        """Mark all notifications as read for the current user."""
        stmt = (
            update(Notification)
            .where(
                Notification.recipient_id == request.user.id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        await db_session.execute(stmt)
        await db_session.commit()
        return {"status": "ok"}
