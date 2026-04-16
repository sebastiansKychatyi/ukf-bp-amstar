"""
Notification Service

Creates, retrieves, and manages in-app notifications.
Designed to be called from other services after business events.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.notification import Notification, NotificationType
from app.services.base import BaseService


class NotificationService(BaseService[Notification]):

    def __init__(self, db: Session):
        super().__init__(db)

    # Creation helpers called from other services

    def notify(
        self,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        related_id: Optional[int] = None,
    ) -> Notification:
        """Create a single notification."""
        n = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            related_id=related_id,
        )
        self.db.add(n)
        self.db.flush()  # flush, not commit — let the caller control the transaction
        self._log_operation("Notification created", user_id=user_id, type=type.value)
        return n

    def notify_many(
        self,
        user_ids: List[int],
        type: NotificationType,
        title: str,
        message: str,
        related_id: Optional[int] = None,
    ) -> List[Notification]:
        """Broadcast the same notification to multiple users."""
        notifications = []
        for uid in user_ids:
            n = Notification(
                user_id=uid,
                type=type,
                title=title,
                message=message,
                related_id=related_id,
            )
            self.db.add(n)
            notifications.append(n)
        self.db.flush()
        return notifications

    # Retrieval

    def get_notifications(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 30,
        unread_only: bool = False,
    ) -> tuple[List[Notification], int, int]:
        """
        Returns (items, total_count, unread_count).
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        unread_count = (
            self.db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .scalar()
        )

        if unread_only:
            query = query.filter(Notification.is_read == False)

        total = query.count()
        items = (
            query
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total, unread_count

    def get_unread_count(self, user_id: int) -> int:
        return (
            self.db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .scalar()
        )

    # Mark as read

    def mark_as_read(self, user_id: int, notification_ids: List[int]) -> int:
        """Mark specific notifications as read. Returns count updated."""
        count = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
                Notification.is_read == False,
            )
            .update({"is_read": True}, synchronize_session="fetch")
        )
        self.db.commit()
        return count

    def mark_all_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True}, synchronize_session="fetch")
        )
        self.db.commit()
        return count
