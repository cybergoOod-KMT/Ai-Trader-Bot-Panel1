from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Position, User
from app.schemas.positions import (
    PositionClosePreviewResponse,
    PositionCloseRequest,
    PositionResponse,
    PositionTpSlRequest,
)
from app.services.order_manager import OrderManager
from app.services.position_monitor import position_monitor_service

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("", response_model=list[PositionResponse])
def list_positions(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PositionResponse]:
    rows = db.scalars(select(Position).order_by(Position.opened_at.desc()).offset(offset).limit(limit)).all()
    return [PositionResponse.model_validate(item) for item in rows]


@router.get("/open", response_model=list[PositionResponse])
def list_open_positions(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PositionResponse]:
    rows = db.scalars(select(Position).where(Position.status == "OPEN").order_by(Position.opened_at.desc()).offset(offset).limit(limit)).all()
    return [PositionResponse.model_validate(item) for item in rows]


@router.post("/{position_id}/close-preview", response_model=PositionClosePreviewResponse)
async def close_position_preview(
    position_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PositionClosePreviewResponse:
    preview = await OrderManager().close_position_preview(db, position_id)
    return PositionClosePreviewResponse(**preview)


@router.post("/{position_id}/close", response_model=PositionResponse)
async def close_position(
    position_id: int,
    payload: PositionCloseRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PositionResponse:
    position = await OrderManager().close_position(db, position_id, payload.confirm_token, request=request, actor_user=current_user)
    return PositionResponse.model_validate(position)


@router.patch("/{position_id}/tp-sl", response_model=PositionResponse)
def update_position_tpsl(
    position_id: int,
    payload: PositionTpSlRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PositionResponse:
    position = OrderManager().update_tpsl(db, position_id, payload.take_profit, payload.stop_loss, request=request, actor_user=current_user)
    return PositionResponse.model_validate(position)


@router.post("/monitor/start")
async def start_position_monitor(_: User = Depends(get_current_user)) -> dict:
    return await position_monitor_service.start()


@router.post("/monitor/stop")
async def stop_position_monitor(_: User = Depends(get_current_user)) -> dict:
    return await position_monitor_service.stop()


@router.get("/monitor/status")
def position_monitor_status(_: User = Depends(get_current_user)) -> dict:
    return position_monitor_service.status()
