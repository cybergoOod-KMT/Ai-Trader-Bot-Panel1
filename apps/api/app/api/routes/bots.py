from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import BotConfig, BotDecision, BotRun, User
from app.schemas.bots import (
    BotConfigRequest,
    BotConfigResponse,
    BotDecisionResponse,
    BotRunResponse,
    BotStartResponse,
    BotStartStopRequest,
)
from app.services.bot_runner import bot_runner_service

router = APIRouter(prefix="/bots", tags=["bots"])


def serialize_config(item: BotConfig) -> BotConfigResponse:
    return BotConfigResponse(
        id=item.id,
        name=item.name,
        mode=item.mode,
        api_account_id=item.api_account_id,
        symbols_json=item.symbols_json,
        max_total_budget_usdt=item.max_total_budget_usdt,
        per_order_usdt=item.per_order_usdt,
        max_open_positions=item.max_open_positions,
        max_daily_loss_pct=item.max_daily_loss_pct,
        min_ai_confidence=item.min_ai_confidence,
        technical_guard_enabled=item.technical_guard_enabled,
        strategy_name=item.strategy_name,
        ai_engine_name=item.ai_engine_name,
        is_active=item.is_active,
        api_error_count=item.api_error_count,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=list[BotConfigResponse])
def list_bots(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[BotConfigResponse]:
    return [serialize_config(item) for item in db.scalars(select(BotConfig).order_by(BotConfig.created_at.desc())).all()]


@router.post("", response_model=BotConfigResponse)
def create_bot(payload: BotConfigRequest, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> BotConfigResponse:
    item = BotConfig(**payload.model_dump(), is_active=False)
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_config(item)


@router.get("/{bot_id}", response_model=BotConfigResponse)
def get_bot(bot_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> BotConfigResponse:
    item = db.get(BotConfig, bot_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot config not found.")
    return serialize_config(item)


@router.patch("/{bot_id}", response_model=BotConfigResponse)
def update_bot(bot_id: int, payload: BotConfigRequest, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> BotConfigResponse:
    item = db.get(BotConfig, bot_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot config not found.")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_config(item)


@router.delete("/{bot_id}")
def delete_bot(bot_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    item = db.get(BotConfig, bot_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot config not found.")
    db.delete(item)
    db.commit()
    return {"success": True}


@router.post("/{bot_id}/start", response_model=BotStartResponse)
async def start_bot(
    bot_id: int,
    payload: BotStartStopRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BotStartResponse:
    return BotStartResponse(**(await bot_runner_service.start_bot(db, bot_id, payload.confirm_token)))


@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return await bot_runner_service.stop_bot(db, bot_id)


@router.get("/{bot_id}/decisions", response_model=list[BotDecisionResponse])
def get_bot_decisions(bot_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[BotDecisionResponse]:
    runs = db.scalars(select(BotRun.id).where(BotRun.bot_config_id == bot_id)).all()
    rows = db.scalars(select(BotDecision).where(BotDecision.bot_run_id.in_(runs)).order_by(BotDecision.created_at.desc())).all() if runs else []
    return [BotDecisionResponse(**item.__dict__) for item in rows]


@router.get("/{bot_id}/runs", response_model=list[BotRunResponse])
def get_bot_runs(bot_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[BotRunResponse]:
    rows = db.scalars(select(BotRun).where(BotRun.bot_config_id == bot_id).order_by(BotRun.started_at.desc())).all()
    return [BotRunResponse(**item.__dict__) for item in rows]
