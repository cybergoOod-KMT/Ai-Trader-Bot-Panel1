from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.risk import RiskCheckRequest, RiskCheckResponse
from app.schemas.technical_guard import TechnicalGuardCheckRequest, TechnicalGuardResponse
from app.services.indicator_engine import build_market_snapshot
from app.services.market_data_service import MarketDataService
from app.services.order_manager import OrderManager
from app.services.technical_guard import TechnicalGuardService

router = APIRouter(tags=["risk"])


@router.post("/risk/check-order", response_model=RiskCheckResponse)
async def check_order_risk(
    payload: RiskCheckRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RiskCheckResponse:
    manager = OrderManager()
    preview = await manager.preview_order(db, payload)
    return RiskCheckResponse(**preview["risk"])


@router.post("/technical-guard/check", response_model=TechnicalGuardResponse)
async def check_technical_guard(
    payload: TechnicalGuardCheckRequest,
    _: User = Depends(get_current_user),
) -> TechnicalGuardResponse:
    service = MarketDataService()
    bundle = await service.get_market_snapshot_bundle(payload.symbol)
    snapshot = build_market_snapshot(bundle.__dict__)
    result = TechnicalGuardService().evaluate(snapshot, "BUY")
    return TechnicalGuardResponse(**result)
