from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User, WatchTask
from app.schemas.watch import WatchTaskResponse

router = APIRouter(prefix="/watch-tasks", tags=["watch-tasks"])


@router.get("", response_model=list[WatchTaskResponse])
def list_watch_tasks(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[WatchTaskResponse]:
    rows = db.scalars(select(WatchTask).order_by(WatchTask.updated_at.desc())).all()
    return [WatchTaskResponse(**item.__dict__) for item in rows]


@router.post("/{task_id}/cancel", response_model=WatchTaskResponse)
def cancel_watch_task(task_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> WatchTaskResponse:
    item = db.get(WatchTask, task_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch task not found.")
    item.status = "CANCELLED"
    db.add(item)
    db.commit()
    db.refresh(item)
    return WatchTaskResponse(**item.__dict__)
