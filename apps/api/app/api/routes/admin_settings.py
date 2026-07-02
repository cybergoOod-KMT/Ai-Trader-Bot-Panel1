from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.admin import GenericSettingsPayload, GenericSettingsResponse
from app.services.audit_service import create_audit_log
from app.services.settings_service import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


def _response(key: str, value: dict) -> GenericSettingsResponse:
    return GenericSettingsResponse(key=key, value=value)


@router.get("/risk", response_model=GenericSettingsResponse)
def get_risk_settings(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GenericSettingsResponse:
    return _response("risk_settings", settings_service.get_risk_settings(db))


@router.put("/risk", response_model=GenericSettingsResponse)
def update_risk_settings(
    payload: GenericSettingsPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericSettingsResponse:
    before = settings_service.get_risk_settings(db)
    row = settings_service.set(db, "risk_settings", {**before, **payload.value})
    create_audit_log(db, "settings.update_risk", "SystemSetting", str(row.id), actor_user=current_user, before=before, after=row.value_json, request=request)
    return _response(row.key, row.value_json)


@router.get("/ai-engines", response_model=GenericSettingsResponse)
def get_ai_engine_settings(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GenericSettingsResponse:
    return _response("ai_engine_settings", settings_service.get_ai_engine_settings(db))


@router.put("/ai-engines", response_model=GenericSettingsResponse)
def update_ai_engine_settings(
    payload: GenericSettingsPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericSettingsResponse:
    before = settings_service.get_ai_engine_settings(db)
    row = settings_service.set(db, "ai_engine_settings", {**before, **payload.value})
    create_audit_log(db, "settings.update_ai_engines", "SystemSetting", str(row.id), actor_user=current_user, before=before, after=row.value_json, request=request)
    return _response(row.key, row.value_json)


@router.get("/strategies", response_model=GenericSettingsResponse)
def get_strategy_settings(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GenericSettingsResponse:
    return _response("strategy_settings", settings_service.get_strategy_settings(db))


@router.put("/strategies", response_model=GenericSettingsResponse)
def update_strategy_settings(
    payload: GenericSettingsPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericSettingsResponse:
    before = settings_service.get_strategy_settings(db)
    row = settings_service.set(db, "strategy_settings", {**before, **payload.value})
    create_audit_log(db, "settings.update_strategies", "SystemSetting", str(row.id), actor_user=current_user, before=before, after=row.value_json, request=request)
    return _response(row.key, row.value_json)


@router.get("/emergency", response_model=GenericSettingsResponse)
def get_emergency_settings(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GenericSettingsResponse:
    return _response("emergency_settings", settings_service.get_emergency_settings(db))


@router.put("/emergency", response_model=GenericSettingsResponse)
def update_emergency_settings(
    payload: GenericSettingsPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericSettingsResponse:
    before = settings_service.get_emergency_settings(db)
    row = settings_service.set(db, "emergency_settings", {**before, **payload.value})
    create_audit_log(db, "settings.update_emergency", "SystemSetting", str(row.id), actor_user=current_user, before=before, after=row.value_json, request=request)
    return _response(row.key, row.value_json)
