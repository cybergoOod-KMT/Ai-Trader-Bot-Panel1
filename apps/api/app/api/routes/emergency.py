from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.admin import EmergencyConfirmRequest
from app.services.audit_service import create_audit_log
from app.services.emergency_service import emergency_service

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.post("/stop-all-bots")
def stop_all_bots(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    result = emergency_service.stop_all_bots(db)
    create_audit_log(db, "emergency.stop_all_bots", "EmergencyAction", "stop_all_bots", actor_user=current_user, after=result, request=request)
    return result


@router.post("/pause-trading")
def pause_trading(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    result = emergency_service.pause_trading(db)
    create_audit_log(db, "emergency.pause_trading", "EmergencyAction", "pause_trading", actor_user=current_user, after=result, request=request)
    return result


@router.post("/resume-trading")
def resume_trading(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    result = emergency_service.resume_trading(db)
    create_audit_log(db, "emergency.resume_trading", "EmergencyAction", "resume_trading", actor_user=current_user, after=result, request=request)
    return result


@router.post("/disable-real-trading")
def disable_real_trading(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    result = emergency_service.disable_real_trading(db)
    create_audit_log(db, "emergency.disable_real_trading", "EmergencyAction", "disable_real_trading", actor_user=current_user, after=result, request=request)
    return result


@router.post("/close-all-dry-run")
async def close_all_dry_run(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    result = await emergency_service.close_all_dry_run(db)
    create_audit_log(db, "emergency.close_all_dry_run", "EmergencyAction", "close_all_dry_run", actor_user=current_user, after=result, request=request)
    return result


@router.post("/close-all-real-preview")
def close_all_real_preview(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    result = emergency_service.close_all_real_preview(db)
    create_audit_log(db, "emergency.close_all_real_preview", "EmergencyAction", "close_all_real_preview", actor_user=current_user, after={"expires_in_seconds": result["expires_in_seconds"]}, request=request)
    return result


@router.post("/close-all-real-confirm")
async def close_all_real_confirm(
    payload: EmergencyConfirmRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = await emergency_service.close_all_real_confirm(db, payload.confirm_token)
    create_audit_log(db, "emergency.close_all_real_confirm", "EmergencyAction", "close_all_real_confirm", actor_user=current_user, after=result, request=request)
    return result
