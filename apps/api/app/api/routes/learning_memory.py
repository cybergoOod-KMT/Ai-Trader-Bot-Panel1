from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import LearningMemory, TradeOutcome, User
from app.schemas.admin import LearningMemoryResponse, TradeOutcomeResponse

router = APIRouter(prefix="/learning-memory", tags=["learning-memory"])


@router.get("", response_model=list[LearningMemoryResponse])
def list_learning_memory(
    symbol: str | None = Query(default=None),
    strategy_name: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LearningMemoryResponse]:
    query = select(LearningMemory).order_by(LearningMemory.updated_at.desc())
    if symbol:
        query = query.where(LearningMemory.symbol == symbol.upper())
    if strategy_name:
        query = query.where(LearningMemory.strategy_name == strategy_name)
    rows = db.scalars(query.offset(offset).limit(limit)).all()
    return [LearningMemoryResponse.model_validate(item, from_attributes=True) for item in rows]


@router.get("/outcomes", response_model=list[TradeOutcomeResponse])
def list_trade_outcomes(
    symbol: str | None = Query(default=None),
    strategy_name: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TradeOutcomeResponse]:
    query = select(TradeOutcome).order_by(TradeOutcome.created_at.desc())
    if symbol:
        query = query.where(TradeOutcome.symbol == symbol.upper())
    if strategy_name:
        query = query.where(TradeOutcome.strategy_name == strategy_name)
    rows = db.scalars(query.offset(offset).limit(limit)).all()
    return [TradeOutcomeResponse.model_validate(item, from_attributes=True) for item in rows]
