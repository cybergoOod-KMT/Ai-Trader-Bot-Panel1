from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Position, User
from app.schemas.strategies import StrategyAnalyzeRequest, StrategyDecisionResponse
from app.services.account_snapshot_service import build_account_snapshot
from app.services.indicator_engine import build_market_snapshot
from app.services.market_data_service import MarketDataService
from app.services.strategy_engine import StrategyEngine

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def list_strategies(_: User = Depends(get_current_user)) -> list[dict]:
    return StrategyEngine().list_strategies()


@router.get("/{name}")
def get_strategy(name: str, _: User = Depends(get_current_user)) -> dict:
    strategy = StrategyEngine().get_strategy(name)
    return {"name": strategy.name}


@router.post("/{name}/analyze", response_model=StrategyDecisionResponse)
async def analyze_strategy(
    name: str,
    payload: StrategyAnalyzeRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StrategyDecisionResponse:
    market_snapshot = build_market_snapshot((await MarketDataService().get_market_snapshot_bundle(payload.symbol)).__dict__)
    account_snapshot = await build_account_snapshot(db)
    open_positions = [
        {"symbol": item.symbol, "quantity": item.quantity, "entry_price": item.entry_price}
        for item in db.scalars(select(Position).where(Position.status == "OPEN")).all()
    ]
    result = StrategyEngine().analyze(name, payload.config, market_snapshot, account_snapshot, open_positions)
    return StrategyDecisionResponse(**result)
