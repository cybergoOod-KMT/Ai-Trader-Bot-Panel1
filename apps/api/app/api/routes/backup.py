from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.admin import BackupResponse
from app.services.audit_service import create_audit_log
from app.services.backup_service import backup_service

router = APIRouter(prefix="/backup", tags=["backup"])


@router.post("/create", response_model=BackupResponse)
def create_backup(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> BackupResponse:
    result = backup_service.create_backup(db)
    create_audit_log(db, "backup.create", "Backup", result["id"], actor_user=current_user, after=result, request=request)
    return BackupResponse(**result)


@router.get("/list", response_model=list[BackupResponse])
def list_backups(_: User = Depends(get_current_user)) -> list[BackupResponse]:
    return [BackupResponse(**item) for item in backup_service.list_backups()]


@router.get("/{backup_id}/download")
def download_backup(backup_id: str, _: User = Depends(get_current_user)) -> FileResponse:
    path = backup_service.download_target(backup_id)
    config_path = path / "config.json"
    target = config_path if config_path.exists() else next(iter(path.iterdir()))
    return FileResponse(path=target, filename=Path(target).name)


@router.post("/{backup_id}/restore")
def restore_backup(
    request: Request,
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = backup_service.restore_backup(backup_id)
    create_audit_log(db, "backup.restore", "Backup", backup_id, actor_user=current_user, after=result, request=request)
    return result
