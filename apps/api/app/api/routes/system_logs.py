from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import SystemLog, User
from app.schemas.logs import SystemLogResponse

router = APIRouter(prefix="/system-logs", tags=["system-logs"])


@router.get("", response_model=list[SystemLogResponse])
def list_system_logs(
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SystemLogResponse]:
    logs = db.scalars(select(SystemLog).order_by(SystemLog.created_at.desc()).limit(limit)).all()
    return [SystemLogResponse.model_validate(log) for log in logs]
