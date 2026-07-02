from sqlalchemy.orm import Session

from app.db.models import Notification
from app.services.ws_manager import ws_manager


def create_notification(
    db: Session,
    notification_type: str,
    title: str,
    message: str,
    metadata: dict | None = None,
    severity: str = "INFO",
) -> Notification:
    notification = Notification(
        type=notification_type,
        severity=severity.upper(),
        title=title,
        message=message,
        metadata_json=metadata,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    import asyncio

    payload = {
        "id": notification.id,
        "type": notification.type,
        "severity": notification.severity,
        "title": notification.title,
        "message": notification.message,
        "is_read": notification.is_read,
        "metadata_json": notification.metadata_json,
        "created_at": notification.created_at.isoformat(),
    }
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.publish("notifications", "notification_created", payload))
    except RuntimeError:
        asyncio.run(ws_manager.publish("notifications", "notification_created", payload))
    return notification
