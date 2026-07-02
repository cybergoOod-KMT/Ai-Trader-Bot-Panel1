from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Notification, User
from app.schemas.notifications import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    notification_type: str | None = Query(default=None, alias="type"),
    severity: str | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NotificationResponse]:
    query = select(Notification).order_by(Notification.created_at.desc())
    if notification_type:
        query = query.where(Notification.type == notification_type)
    if severity:
        query = query.where(Notification.severity == severity.upper())
    if is_read is not None:
        query = query.where(Notification.is_read.is_(is_read))
    items = db.scalars(query.limit(limit)).all()
    return [NotificationResponse.model_validate(item) for item in items]


@router.post("/{notification_id}/mark-read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read")
def mark_all_read(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = db.scalars(select(Notification).where(Notification.is_read.is_(False))).all()
    for item in items:
        item.is_read = True
        db.add(item)
    db.commit()
    return {"updated": len(items)}
