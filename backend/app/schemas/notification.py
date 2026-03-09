"""
Notification Schemas
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    related_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationMarkRead(BaseModel):
    notification_ids: List[int] = Field(..., description="IDs of notifications to mark as read")
