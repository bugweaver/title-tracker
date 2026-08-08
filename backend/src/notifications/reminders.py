"""Lazy reminder helpers for on-hold and new-release notifications."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Notification, NotificationType, UserTitle, UserTitleStatus

ON_HOLD_REMINDER_DAYS = 30

# Statuses that should receive new season/DLC release alerts
NEW_RELEASE_STATUSES = (
    UserTitleStatus.COMPLETED,
    UserTitleStatus.PLAYING,
    UserTitleStatus.WATCHING,
    UserTitleStatus.PLANNED,
    UserTitleStatus.ON_HOLD,
)


async def ensure_on_hold_reminders(
    db_session: AsyncSession,
    user_id: int,
) -> int:
    """Create on-hold reminders for titles paused longer than the threshold.

    Returns the number of newly created notifications.
    """
    threshold = datetime.utcnow() - timedelta(days=ON_HOLD_REMINDER_DAYS)

    stmt = select(UserTitle).where(
        UserTitle.user_id == user_id,
        UserTitle.status == UserTitleStatus.ON_HOLD,
        UserTitle.updated_at <= threshold,
    )
    result = await db_session.execute(stmt)
    stale_titles = list(result.scalars().all())
    if not stale_titles:
        return 0

    created = 0
    for user_title in stale_titles:
        recent_stmt = (
            select(Notification.id)
            .where(
                Notification.recipient_id == user_id,
                Notification.user_title_id == user_title.id,
                Notification.type == NotificationType.ON_HOLD_REMINDER,
                Notification.created_at >= threshold,
            )
            .limit(1)
        )
        recent_result = await db_session.execute(recent_stmt)
        if recent_result.scalar_one_or_none() is not None:
            continue

        db_session.add(
            Notification(
                recipient_id=user_id,
                actor_id=user_id,
                user_title_id=user_title.id,
                type=NotificationType.ON_HOLD_REMINDER,
            )
        )
        created += 1

    if created:
        await db_session.flush()
    return created


async def notify_title_owners_of_new_release(
    db_session: AsyncSession,
    title_id: int,
    *,
    actor_user_id: int | None = None,
) -> int:
    """Notify library owners that new catalog content appeared for a title."""
    stmt = select(UserTitle).where(
        UserTitle.title_id == title_id,
        UserTitle.status.in_(NEW_RELEASE_STATUSES),
    )
    result = await db_session.execute(stmt)
    owners = list(result.scalars().all())
    if not owners:
        return 0

    # Avoid spamming: skip if an unread new_release already exists for this entry
    created = 0
    for user_title in owners:
        existing_stmt = (
            select(Notification.id)
            .where(
                Notification.recipient_id == user_title.user_id,
                Notification.user_title_id == user_title.id,
                Notification.type == NotificationType.NEW_RELEASE,
                Notification.is_read == False,  # noqa: E712
            )
            .limit(1)
        )
        existing_result = await db_session.execute(existing_stmt)
        if existing_result.scalar_one_or_none() is not None:
            continue

        db_session.add(
            Notification(
                recipient_id=user_title.user_id,
                actor_id=actor_user_id or user_title.user_id,
                user_title_id=user_title.id,
                type=NotificationType.NEW_RELEASE,
            )
        )
        created += 1

    if created:
        await db_session.flush()
    return created
