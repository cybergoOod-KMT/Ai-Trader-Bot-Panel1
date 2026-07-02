import logging

from sqlalchemy.orm import Session

from app.db.models import SystemLog
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


def create_system_log(db: Session, level: str, source: str, message: str, metadata: dict | None = None) -> SystemLog:
    log = SystemLog(level=level, source=source, message=message, metadata_json=metadata)
    db.add(log)
    db.commit()
    db.refresh(log)
    logger.log(getattr(logging, level.upper(), logging.INFO), "%s: %s", source, message)
    import asyncio

    payload = {
        "id": log.id,
        "level": log.level,
        "source": log.source,
        "message": log.message,
        "metadata_json": log.metadata_json,
        "created_at": log.created_at.isoformat(),
    }
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.publish("system_logs", "system_log_created", payload))
    except RuntimeError:
        asyncio.run(ws_manager.publish("system_logs", "system_log_created", payload))
    return log
