"""
Notification API Endpoints

Provides notification list, unread count, and mark-as-read operations.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkRead,
)

router = APIRouter()


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="Get current user's notifications",
)
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = NotificationService(db)
    items, total, unread_count = svc.get_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
    )


@router.get(
    "/unread-count",
    summary="Get unread notification count",
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = NotificationService(db)
    return {"unread_count": svc.get_unread_count(current_user.id)}


@router.put(
    "/read",
    summary="Mark specific notifications as read",
)
def mark_as_read(
    payload: NotificationMarkRead,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = NotificationService(db)
    count = svc.mark_as_read(current_user.id, payload.notification_ids)
    return {"updated": count}


@router.put(
    "/read-all",
    summary="Mark all notifications as read",
)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = NotificationService(db)
    count = svc.mark_all_read(current_user.id)
    return {"updated": count}
